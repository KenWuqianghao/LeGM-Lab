# ruff: noqa: E501, B008
"""Modal deployment for LeLM — OpenAI-compatible inference endpoint.

Serves the LeLM GGUF model via llama-cpp-python with an OpenAI-compatible
chat completions API. The bot connects using the existing openai_compat
LLM provider — no code changes needed, just set env vars.

Deploy:
    modal deploy deploy/modal_lelm.py

Test:
    curl -X POST <MODAL_URL>/v1/chat/completions
        -H "Authorization: Bearer <AUTH_TOKEN>"
        -H "Content-Type: application/json"
        -d '{"model":"lelm","messages":[{"role":"user","content":"Is LeBron washed?"}]}'

Bot config (Railway env vars):
    LLM_PROVIDER=openai_compat
    OPENAI_COMPAT_BASE_URL=<MODAL_URL>/v1
    OPENAI_COMPAT_API_KEY=<AUTH_TOKEN>
    OPENAI_COMPAT_MODEL=lelm
"""

import modal

GGUF_REPO = "KenWu/LeLM-GGUF"
GGUF_FILE = "LeLM-Q4_K_M.gguf"
MODEL_DIR = "/models"

_download_cmd = (
    'python -c "'
    "from huggingface_hub import hf_hub_download; "
    f"hf_hub_download('{GGUF_REPO}', '{GGUF_FILE}', local_dir='{MODEL_DIR}')"
    '"'
)

image = modal.Image.from_registry(
    "nvidia/cuda:12.4.1-runtime-ubuntu22.04",
    add_python="3.12",
).run_commands(
    "apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*",
    "pip install huggingface-hub 'fastapi>=0.115' 'pydantic>=2'",
    "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124",
    _download_cmd,
)

app = modal.App("lelm-inference", image=image)

GPU = "T4"


@app.cls(
    gpu=GPU,
    scaledown_window=300,
    secrets=[modal.Secret.from_name("lelm-auth", required_keys=["AUTH_TOKEN"])],
)
@modal.concurrent(max_inputs=4)
class LeLMModel:
    """Serves LeLM via llama-cpp-python with OpenAI-compatible API."""

    @modal.enter()
    def load_model(self) -> None:
        import os

        from llama_cpp import Llama

        model_path = os.path.join(MODEL_DIR, GGUF_FILE)
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=2048,
            verbose=False,
        )
        self.auth_token = os.environ["AUTH_TOKEN"]

    @modal.asgi_app()
    def serve(self):
        import re
        import time
        import uuid

        from fastapi import Depends, FastAPI, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
        from pydantic import BaseModel, Field

        think_re = re.compile(r"<think>[\s\S]*?</think>\s*")

        web_app = FastAPI(title="LeLM Inference")
        auth_scheme = HTTPBearer()

        model_ref = self

        class ChatMessage(BaseModel):
            role: str
            content: str

        class ChatRequest(BaseModel):
            model: str = "lelm"
            messages: list[ChatMessage]
            max_tokens: int = Field(default=512, le=2048)
            temperature: float = Field(default=0.7, ge=0.0, le=2.0)
            top_p: float = Field(default=0.9, ge=0.0, le=1.0)

        def verify_token(
            token: HTTPAuthorizationCredentials = Depends(auth_scheme),
        ) -> str:
            if token.credentials != model_ref.auth_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid auth token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token.credentials

        @web_app.post("/v1/chat/completions")
        def chat_completions(
            req: ChatRequest,
            _token: str = Depends(verify_token),
        ) -> dict:
            messages = [{"role": m.role, "content": m.content} for m in req.messages]
            response = model_ref.llm.create_chat_completion(
                messages=messages,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
            )

            # Strip Qwen3 <think> tokens from output
            msg = response["choices"][0]["message"]
            if msg.get("content"):
                msg["content"] = think_re.sub("", msg["content"]).strip()

            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "lelm",
                "choices": [
                    {
                        "index": 0,
                        "message": msg,
                        "finish_reason": response["choices"][0].get(
                            "finish_reason", "stop"
                        ),
                    }
                ],
                "usage": response.get("usage", {}),
            }

        @web_app.get("/health")
        def health() -> dict:
            return {"status": "ok"}

        return web_app

"""Tests for the LeLM Modal provider."""

import pytest
import respx
from httpx import Response

from legm.llm.lelm_modal import LeLMModalProvider, _parse_response
from legm.llm.types import Message


def test_parse_response_strips_thinking_blocks() -> None:
    """Thinking tokens should be removed from assistant content."""
    data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": (
                        "<think>internal</think>\n\n"
                        "Bro is not washed."
                    ),
                },
                "finish_reason": "stop",
            }
        ]
    }

    result = _parse_response(data)

    assert result.content == "Bro is not washed."
    assert result.stop_reason == "stop"


@respx.mock
@pytest.mark.asyncio
async def test_generate_posts_to_modal_root(respx_mock: respx.MockRouter) -> None:
    """Provider should POST to the Modal root URL, not /v1/chat/completions."""
    base_url = "https://example--lelm-lelm-chat.modal.run"
    route = respx_mock.post(base_url).mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Valid take."},
                        "finish_reason": "stop",
                    }
                ]
            },
        )
    )

    provider = LeLMModalProvider(base_url=base_url, model="lelm")
    result = await provider.generate(
        messages=[Message(role="user", content="Test take")],
    )

    assert route.called
    assert result.content == "Valid take."

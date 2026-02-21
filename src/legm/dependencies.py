"""FastAPI dependency injection wiring."""

from typing import Annotated

from fastapi import Depends, Request

from legm.agent.analyzer import TakeAnalyzer
from legm.db.repository import TakeRepository


def get_take_repository(request: Request) -> TakeRepository:
    """Retrieve the TakeRepository from app state."""
    return request.app.state.take_repository


def get_take_analyzer(request: Request) -> TakeAnalyzer:
    """Retrieve the TakeAnalyzer from app state."""
    return request.app.state.take_analyzer


TakeRepositoryDep = Annotated[TakeRepository, Depends(get_take_repository)]
TakeAnalyzerDep = Annotated[TakeAnalyzer, Depends(get_take_analyzer)]

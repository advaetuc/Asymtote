"""The Phase 0 health contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health describes the API process, not numerical feature availability."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]
    api_version: str

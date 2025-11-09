"""Domain models for CTTI Endpoint Selection Facilitator."""
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Anchors(BaseModel):
    """High and low anchors for a criterion."""

    hi: str = Field(..., description="High anchor description")
    lo: str = Field(..., description="Low anchor description")


class Criterion(BaseModel):
    """A scoring criterion with weight and anchors."""

    id: str = Field(..., description="Unique identifier for the criterion")
    name: str = Field(..., description="Display name of the criterion")
    weight: int = Field(..., ge=0, description="Weight of the criterion (must be >= 0)")
    anchors: Anchors = Field(..., description="High and low anchor descriptions")
    active: bool = Field(True, description="Whether the criterion is active")

    @field_validator("weight")
    @classmethod
    def weight_non_negative(cls, v: int) -> int:
        """Validate that weight is non-negative."""
        if v < 0:
            raise ValueError("Weight must be non-negative")
        return v


class Option(BaseModel):
    """An option/alternative to be scored."""

    id: str = Field(..., description="Unique identifier for the option")
    name: str = Field(..., description="Display name of the option")
    notes: Optional[str] = Field(None, description="Optional notes about the option")


class Score(BaseModel):
    """A score for an option on a specific criterion."""

    optionId: str = Field(..., description="ID of the option being scored")
    criterionId: str = Field(..., description="ID of the criterion being scored on")
    raw: int = Field(..., ge=1, le=5, description="Raw score value between 1 and 5")
    rationale: Optional[str] = Field(None, description="Optional rationale for the score")

    @field_validator("raw")
    @classmethod
    def validate_raw_score(cls, v: int) -> int:
        """Validate that raw score is between 1 and 5."""
        if not 1 <= v <= 5:
            raise ValueError("Raw score must be between 1 and 5")
        return v


class AuditEvent(BaseModel):
    """An audit event tracking changes to the scenario."""

    ts: datetime = Field(default_factory=datetime.now, description="Timestamp of the event")
    actor: str = Field(..., description="Actor who triggered the event")
    type: str = Field(..., description="Type of event")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details about the event"
    )


class Settings(BaseModel):
    """Settings for scenario behavior."""

    rationalePolicy: Literal["required", "optional", "skippable"] = Field(
        "optional", description="Policy for rationale entry"
    )
    flowDefault: Literal["by_criterion", "by_option"] = Field(
        "by_criterion", description="Default scoring flow"
    )
    sensitivityStep: float = Field(
        1.0, gt=0, description="Step size for sensitivity analysis in percent"
    )


class Scenario(BaseModel):
    """A complete scoring scenario."""

    id: str = Field(..., description="Unique identifier for the scenario")
    title: str = Field(..., description="Title of the scenario")
    createdAt: datetime = Field(
        default_factory=datetime.now, description="When the scenario was created"
    )
    modifiedAt: datetime = Field(
        default_factory=datetime.now, description="When the scenario was last modified"
    )
    weightsLocked: bool = Field(False, description="Whether weights are locked")
    criteria: list[Criterion] = Field(default_factory=list, description="List of criteria")
    options: list[Option] = Field(default_factory=list, description="List of options")
    scores: list[Score] = Field(default_factory=list, description="List of scores")
    settings: Settings = Field(default_factory=Settings, description="Scenario settings")
    audit: list[AuditEvent] = Field(default_factory=list, description="Audit trail")

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class CropInput(BaseModel):
    N: float = Field(ge=0)
    P: float = Field(ge=0)
    K: float = Field(ge=0)
    temperature: float
    humidity: float = Field(ge=0, le=100)
    ph: float = Field(ge=0, le=14)
    rainfall: float = Field(ge=0)


class YieldInput(BaseModel):
    State_Name: str
    District_Name: str
    Crop_Year: int = Field(ge=1990, le=2100)
    Season: str
    Crop: str
    Area: float = Field(gt=0)


class RoverCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(min_length=3, max_length=80)
    action: str = Field(min_length=3, max_length=60)
    parameters: dict[str, Any] = Field(default_factory=dict)
    nonce: str = Field(min_length=8, max_length=100)
    issued_at: float


class CropResponse(BaseModel):
    recommended_crop: str
    confidence: float
    alternatives: list[dict[str, Any]]


class DiseaseResponse(BaseModel):
    crop: str
    disease: str
    confidence: float
    raw_label: str | None = None
    health_status: str
    treatment: str
    precautions: list[str]
    prevention: list[str]


class YieldResponse(BaseModel):
    predicted_production: float
    input_used: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
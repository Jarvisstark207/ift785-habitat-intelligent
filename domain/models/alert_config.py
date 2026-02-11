from pydantic import BaseModel, Field
from typing import Optional


class TemperatureConfig(BaseModel):
    min: Optional[float] = Field(None, ge=0, le=50)
    max: Optional[float] = Field(None, ge=0, le=50)


class ConsumptionConfig(BaseModel):
    max: Optional[float] = Field(None, ge=0)


class AlertConfigUpdate(BaseModel):
    temperature: Optional[TemperatureConfig] = None
    consumption: Optional[ConsumptionConfig] = None

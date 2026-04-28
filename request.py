from pydantic import BaseModel, field_validator
from datetime import datetime

class EncounterRequest(BaseModel):
    customer_id: str

class SymptomRequest(BaseModel):
    encounter_id: str
    symptoms: str

class FHIRRequest(BaseModel):
    encounter_id: str
    patientName: str
    birthDate: str

    @field_validator('birthDate')
    @classmethod
    def validate_birthdate_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('birthDate must be in YYYY-MM-DD format')
        return v
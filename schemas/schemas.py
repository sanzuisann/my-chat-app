# schemas.py
from pydantic import BaseModel

class CharacterCreate(BaseModel):
    name: str
    personality: str
    system_prompt: str

class CharacterResponse(BaseModel):
    id: int
    name: str
    personality: str
    system_prompt: str

    class Config:
        orm_mode = True

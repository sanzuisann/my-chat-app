# crud.py
from sqlalchemy.orm import Session
from models.models import Character
from schemas import CharacterCreate

def create_character(db: Session, character: CharacterCreate):
    db_character = Character(
        name=character.name,
        personality=character.personality,
        system_prompt=character.system_prompt
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

def get_character_by_name(db: Session, name: str):
    return db.query(Character).filter(Character.name == name).first()

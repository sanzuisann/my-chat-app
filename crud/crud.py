import json
from sqlalchemy.orm import Session
from models.models import Character
from schemas.schemas import CharacterCreate
from typing import List

# 🔸 キャラ新規作成（構造データをJSON文字列に変換して保存）
def create_character(db: Session, character: CharacterCreate) -> Character:
    db_character = Character(
        name=character.name,
        personality=character.personality,
        system_prompt=character.system_prompt,
        background=character.background,
        tone=character.tone,
        world=character.world,
        prohibited=json.dumps(character.prohibited) if character.prohibited else None,
        examples=json.dumps(character.examples) if character.examples else None
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

# 🔹 名前でキャラ取得
def get_character_by_name(db: Session, name: str) -> Character | None:
    return db.query(Character).filter(Character.name == name).first()

# 🔹 全キャラ取得
def get_all_characters(db: Session) -> List[Character]:
    return db.query(Character).all()

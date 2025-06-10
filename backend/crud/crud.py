import json
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.models import Character, Construct
from backend.schemas.schemas import CharacterCreate, ConstructCreate

# 🔸 キャラ新規作成
def create_character(db: Session, character: CharacterCreate) -> Character:
    db_character = Character(
        name=character.name,
        personality=character.personality,
        system_prompt=character.system_prompt,
        background=character.background,
        tone=character.tone,
        world=character.world,
        prohibited=json.dumps(character.prohibited) if character.prohibited else None,
        examples=json.dumps(character.examples) if character.examples else None,
        openness=character.openness,
        conscientiousness=character.conscientiousness,
        extraversion=character.extraversion,
        agreeableness=character.agreeableness,
        neuroticism=character.neuroticism
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

# 🔹 名前でキャラ取得
def get_character_by_name(db: Session, name: str) -> Optional[Character]:
    return db.query(Character).filter(Character.name == name).first()

# 🔹 全キャラ取得
def get_all_characters(db: Session) -> List[Character]:
    return db.query(Character).all()

# 🔸 コンストラクト作成
def create_construct(db: Session, data: ConstructCreate) -> Construct:
    construct = Construct(
        user_id=data.user_id,
        character_id=data.character_id,
        axis=json.dumps(data.axis),
        name=data.name,
        importance=data.importance,
        behavior_effect=data.behavior_effect,
        value=data.value,
    )
    db.add(construct)
    db.commit()
    db.refresh(construct)
    return construct


# 🔸 複数コンストラクト作成
def create_constructs(db: Session, constructs: List[ConstructCreate]) -> List[Construct]:
    objs = []
    for data in constructs:
        obj = Construct(
            user_id=data.user_id,
            character_id=data.character_id,
            axis=json.dumps(data.axis),
            name=data.name,
            importance=data.importance,
            behavior_effect=data.behavior_effect,
            value=data.value,
        )
        db.add(obj)
        objs.append(obj)
    db.commit()
    for obj in objs:
        db.refresh(obj)
    return objs


# 🔹 指定ユーザー・キャラのコンストラクト一覧
def get_constructs(db: Session, user_id, character_id) -> List[Construct]:
    return (
        db.query(Construct)
        .filter(Construct.user_id == user_id, Construct.character_id == character_id)
        .all()
    )


# 🔹 コンストラクト削除
def delete_construct(db: Session, construct_id):
    c = db.query(Construct).filter(Construct.id == construct_id).first()
    if c:
        db.delete(c)
        db.commit()
    return c

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


settings.ensure_dirs()
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_sqlite_compat_schema() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "generated_images" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("generated_images")}
    columns = {
        "plan_id": "INTEGER",
        "platform": "VARCHAR(80)",
        "generation_mode": "VARCHAR(80)",
        "prompt_pack_id": "VARCHAR(120)",
        "prompt_pack_json": "TEXT",
        "is_recommended": "BOOLEAN NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for name, ddl in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE generated_images ADD COLUMN {name} {ddl}"))

    if "image_reviews" not in inspector.get_table_names():
        return
    review_existing = {column["name"] for column in inspector.get_columns("image_reviews")}
    review_columns = {
        "product_consistency_score": "INTEGER NOT NULL DEFAULT 80",
        "text_artifact_risk": "VARCHAR(40) NOT NULL DEFAULT 'low'",
        "ai_artifact_risk": "VARCHAR(40) NOT NULL DEFAULT 'low'",
        "recommendation_level": "VARCHAR(40) NOT NULL DEFAULT 'usable'",
    }
    with engine.begin() as connection:
        for name, ddl in review_columns.items():
            if name not in review_existing:
                connection.execute(text(f"ALTER TABLE image_reviews ADD COLUMN {name} {ddl}"))

    if "copywriting" not in inspector.get_table_names():
        return
    copy_existing = {column["name"] for column in inspector.get_columns("copywriting")}
    if "douyin_script" not in copy_existing:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE copywriting ADD COLUMN douyin_script TEXT NOT NULL DEFAULT ''"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

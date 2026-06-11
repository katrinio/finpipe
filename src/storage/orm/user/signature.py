"""ORM-сущность сохранённой подписи."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Boolean, Integer, String, delete, func, select, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel
from src.utils.credentials import LOGGER


class Signature(BaseModel):
    """Сохранённая подпись владельца."""

    __tablename__ = "signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    signature_path: Mapped[str] = mapped_column(String, nullable=False)
    signature_hash: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    @classmethod
    def create(
        cls,
        owner_telegram_id: int,
        signature_path: Path | str,
        signature_hash: str | None = None,
        active: bool = True,
    ) -> None:
        """Создаёт или обновляет подпись владельца без дублей."""

        resolved_signature_path = str(signature_path)
        resolved_signature_hash = signature_hash or cls._hash_path(signature_path)
        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)
            signature = session.scalar(statement)

            if signature is None:
                session.add(
                    cls(
                        owner_telegram_id=owner_telegram_id,
                        signature_path=resolved_signature_path,
                        signature_hash=resolved_signature_hash,
                        active=active,
                    )
                )
                LOGGER.info("Created signature for Telegram user %s: %s", owner_telegram_id, resolved_signature_path)
            else:
                signature.signature_path = resolved_signature_path
                signature.signature_hash = resolved_signature_hash
                signature.active = active
                signature.updated_at = datetime.now(UTC)
                LOGGER.info("Updated signature for Telegram user %s: %s", owner_telegram_id, resolved_signature_path)

            session.commit()

    @classmethod
    def get_active(cls, owner_telegram_id: int) -> "Signature | None":
        """Возвращает активную подпись владельца, если она есть."""

        with cls.session() as session:
            statement = (
                select(cls)
                .where(
                    cls.owner_telegram_id == owner_telegram_id,
                    cls.active.is_(True),
                )
                .limit(1)
            )
            return session.scalar(statement)

    @classmethod
    def get_by_owner(cls, owner_telegram_id: int) -> "Signature | None":
        """Возвращает подпись владельца независимо от активного статуса."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)
            return session.scalar(statement)

    @classmethod
    def exists(cls, owner_telegram_id: int) -> bool:
        """Проверяет наличие подписи для владельца."""

        return cls.get_by_owner(owner_telegram_id) is not None

    @classmethod
    def delete(cls, owner_telegram_id: int) -> None:
        """Очищает активную подпись владельца, если она есть."""

        with cls.session() as session:
            statement = select(cls).where(cls.owner_telegram_id == owner_telegram_id).limit(1)
            signature = session.scalar(statement)
            if signature is None:
                return

            signature_path = Path(signature.signature_path)
            session.execute(delete(cls).where(cls.owner_telegram_id == owner_telegram_id))
            session.commit()

            if signature_path.exists():
                signature_path.unlink()

    @staticmethod
    def _hash_path(signature_path: Path | str) -> str:
        path = Path(signature_path)
        return hashlib.sha256(path.read_bytes()).hexdigest()

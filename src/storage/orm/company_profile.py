"""ORM-сущность пользовательских настроек."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime

from src.storage.orm.base import BaseModel


class CompanyProfile(BaseModel):
    """CompanyProfile."""

    __tablename__ = "company_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String)
    company_address: Mapped[str] = mapped_column(String)
    service_agreement_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)

from __future__ import annotations

from typing import Optional

from .db import Base, TimeID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, JSON

class Finding(TimeID):
    __tablename__ = "findings"
    scan_id: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

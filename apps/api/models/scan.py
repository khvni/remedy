from __future__ import annotations

from typing import Optional

from .db import Base, TimeID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON

class Scan(TimeID):
    __tablename__ = "scans"
    repo_id: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)  # 'sast' | 'sca'
    status: Mapped[str] = mapped_column(String, default="queued")
    findings_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

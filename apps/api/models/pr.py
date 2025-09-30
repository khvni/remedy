from __future__ import annotations

from typing import Optional

from .db import Base, TimeID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text

class PullRequest(TimeID):
    __tablename__ = "pull_requests"
    repo_id: Mapped[str] = mapped_column(String)
    branch: Mapped[str] = mapped_column(String)
    pr_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

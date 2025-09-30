from __future__ import annotations

from typing import Optional

from .db import Base, TimeID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class Repo(TimeID):
    __tablename__ = "repos"
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    default_branch: Mapped[Optional[str]] = mapped_column(String, nullable=True)

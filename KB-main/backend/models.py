"""
SQLAlchemy ORM models for EKIP.
Tables: users, roles, user_roles, documents, access_audit_log.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey,
    Table, ARRAY
)
from sqlalchemy.orm import relationship
from backend.database import Base


# ── Association table: user <-> role (many-to-many) ──
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.user_id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.role_id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def role_names(self):
        return [r.role_name for r in self.roles]


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=False)
    department = Column(String, nullable=False)
    classification = Column(String, nullable=False)  # "public" or "restricted"
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AccessAuditLog(Base):
    __tablename__ = "access_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    query_text = Column(Text)
    doc_ids = Column(Text)  # stored as comma-separated UUIDs for portability
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    allowed = Column(Boolean, nullable=False, default=True)

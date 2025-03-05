import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.postgres import Base


class Permission(Base):
    __tablename__ = "permission"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

    # Связь с ролями
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
import uuid
from typing import Optional

from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from src.db.postgres import Base

# Ассоциативная таблица для связи пользователей и ролей


class UserRoles(Base):
    __tablename__ = 'user_roles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))


class User(Base):
    """
    Модель пользователя. Содержит основную информацию о пользователе,
    а также связанные роли и организацию.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(255), unique=True, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

    roles = relationship("Role", secondary=UserRoles.__table__, back_populates="users")
    organization = relationship("Organization", back_populates="users")

    def __init__(self, username: str,
                 password: str,
                 email: str,
                 first_name: str = "",
                 last_name: str = "",
                 is_active: bool = True,
                 is_superuser: bool = False,
                 organization_id: Optional[UUID] = None
                 ) -> None:
        self.username = username
        self.hashed_password = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_active = is_active
        self.is_superuser = is_superuser
        self.organization_id = organization_id

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.hashed_password, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Role(Base):
    """
    Модель роли пользователя. Содержит название роли и описание
    """
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", secondary=UserRoles.__table__, back_populates="roles")

    def __repr__(self) -> str:
        return f'<Role {self.name}>'


class Organization(Base):
    """
    Модель организации. Содержит название и описание организации
    """
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="organization")
    patients = relationship("Patient", back_populates="organization")

    def __repr__(self) -> str:
        return f'<Organization {self.name}>'
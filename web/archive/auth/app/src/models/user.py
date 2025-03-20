import uuid

from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from src.db.postgres import Base
from src.models.role import Role

# Ассоциативная таблица для связи пользователей и ролей
user_roles = Table('user_roles', Base.metadata,
                   Column('user_id', UUID(as_uuid=True), ForeignKey('user.id', ondelete="CASCADE")),
                   Column('role_id', UUID(as_uuid=True), ForeignKey('role.id', ondelete="CASCADE"))
                   )


class User(Base):
    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"), nullable=True)

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    organization = relationship("Organization", back_populates="users")

    def __init__(self, login: str, password: str, email: str, first_name: str = "", last_name: str = "", is_superuser: bool = False) -> None:
        self.login = login
        self.password = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_superuser = is_superuser

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def __repr__(self) -> str:
        return f'<User {self.login}>'


class Organization(Base):
    __tablename__ = "organization"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    users = relationship("User", back_populates="organization")

    def __repr__(self) -> str:
        return f'<Organization {self.name}>'
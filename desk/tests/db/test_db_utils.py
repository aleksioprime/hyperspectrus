import pytest
from desk.src.db.models import User
from desk.src.db.db import has_users
from desk.src.db import db as main_db_module # For monkeypatching SessionLocal

# The db_session fixture from conftest.py is used implicitly by pytest for tests that need it.

def test_has_users_false_when_empty(db_session, monkeypatch):
    """
    Test that has_users() returns False when the database is empty.
    """
    # Ensure that has_users() uses the same session factory as the test's db_session
    # db_session.bind is the engine, db_session.bind.sessionmaker is the factory
    # However, db_session itself is a session instance. Its factory is db_session.session_factory
    monkeypatch.setattr(main_db_module, 'SessionLocal', db_session.session_factory)
    
    assert not has_users()

def test_has_users_true_when_users_exist(db_session, monkeypatch):
    """
    Test that has_users() returns True when there are users in the database.
    """
    monkeypatch.setattr(main_db_module, 'SessionLocal', db_session.session_factory)
    
    # Create a user
    user = User(
        username="testuser_has_users",
        hashed_password="password123",
        email="test_has_users@example.com",
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    
    assert has_users()

def test_has_users_false_after_users_deleted(db_session, monkeypatch):
    """
    Test that has_users() returns False after users are added and then deleted.
    """
    monkeypatch.setattr(main_db_module, 'SessionLocal', db_session.session_factory)
    
    # 1. Create a user and verify has_users is True
    user = User(
        username="delete_test_user",
        hashed_password="password123",
        email="delete_test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    
    assert has_users(), "has_users should be True after adding a user"
    
    # 2. Delete the user
    db_session.delete(user)
    db_session.commit()
    
    assert not has_users(), "has_users should be False after deleting the user"

def test_has_users_with_multiple_users_then_delete_one(db_session, monkeypatch):
    """
    Test has_users with multiple users, then delete one, should still be true.
    Then delete all, should be false.
    """
    monkeypatch.setattr(main_db_module, 'SessionLocal', db_session.session_factory)

    user1 = User(username="user1_multi", email="u1m@example.com", hashed_password="p1")
    user2 = User(username="user2_multi", email="u2m@example.com", hashed_password="p2")
    db_session.add_all([user1, user2])
    db_session.commit()

    assert has_users(), "has_users should be True with multiple users"

    # Delete one user
    db_session.delete(user1)
    db_session.commit()
    assert has_users(), "has_users should still be True after deleting one of multiple users"

    # Delete the second user
    db_session.delete(user2)
    db_session.commit()
    assert not has_users(), "has_users should be False after deleting all users"

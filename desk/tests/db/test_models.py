import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict

# Adjust the import path based on the actual location of your models
# Assuming 'desk/src/' is in PYTHONPATH or tests are run from 'desk/' root
from src.db.models import Base, User, Patient, Session, Device, DeviceBinding # Add other models as needed for tests
from src.db.db import SessionLocal # To compare or use if needed, but test will use its own session

class BaseDbTestCase(unittest.TestCase):
    engine = None
    Session = None # Class variable for the session factory
    db: SQLAlchemySession = None # Instance variable for the actual session

    @classmethod
    def setUpClass(cls):
        '''
        Set up an in-memory SQLite database for the entire test class (all test methods).
        This is more efficient than per-test setup if table creation is slow,
        but requires careful test isolation if tests modify data they don't clean up.
        For simplicity now, we'll use it, but per-test setup (setUp method) is also common.
        '''
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine) # Create all tables from your models
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        '''
        Dispose of the engine after all tests in the class have run.
        '''
        if cls.engine:
            cls.engine.dispose()

    def setUp(self):
        '''
        Create a new database session before each test method.
        This ensures each test runs with a clean session and can be rolled back.
        '''
        self.db = self.Session()

    def tearDown(self):
        '''
        Rollback any changes and close the session after each test method.
        This ensures tests are isolated from each other.
        '''
        if self.db:
            self.db.rollback() # Rollback any uncommitted changes
            self.db.close()


class TestUserPatientSession(BaseDbTestCase):

    def test_create_user(self):
        # Test creating a User instance
        user_data = {
            "username": "testuser",
            "hashed_password": "password123",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        retrieved_user = self.db.query(User).filter_by(username="testuser").first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, user_data["email"])
        self.assertEqual(retrieved_user.full_name, "Test User")
        self.assertTrue(retrieved_user.is_active) # Default value check
        self.assertFalse(retrieved_user.is_superuser) # Default value check

    def test_create_patient(self):
        # Test creating a Patient instance
        from datetime import date
        patient_data = {
            "full_name": "John Doe",
            "birth_date": date(1990, 1, 1),
            "notes": "Test patient notes"
        }
        patient = Patient(**patient_data)
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)

        retrieved_patient = self.db.query(Patient).filter_by(full_name="John Doe").first()
        self.assertIsNotNone(retrieved_patient)
        self.assertEqual(retrieved_patient.birth_date, patient_data["birth_date"])
        self.assertIsNotNone(retrieved_patient.created_at)

    def test_create_session_with_patient_and_operator(self):
        # Test creating a Session linked to a Patient and User (operator)
        from datetime import date, datetime

        # 1. Create Operator (User)
        op_user = User(
            username="operator",
            hashed_password="op_password",
            email="operator@example.com",
            first_name="Op",
            last_name="Erator"
        )
        self.db.add(op_user)
        self.db.commit() # Commit early to get op_user.id

        # 2. Create Patient
        patient = Patient(
            full_name="Session Patient",
            birth_date=date(1985, 5, 15)
        )
        self.db.add(patient)
        self.db.commit() # Commit early to get patient.id

        # 3. Create Device and DeviceBinding (minimal for relationship)
        # Ensure Device model is imported in BaseDbTestCase or here
        device = Device(name="Test Device for Session")
        self.db.add(device)
        self.db.commit() # Commit for device.id

        device_binding = DeviceBinding(
            user_id=op_user.id, # Use the actual ID from the committed user
            device_id=device.id, # Use the actual ID from the committed device
            ip_address="127.0.0.1"
        )
        self.db.add(device_binding)
        self.db.commit() # Commit for device_binding.id

        # 4. Create Session
        session_notes = "Test session notes"
        session = Session(
            patient_id=patient.id, # Use actual patient.id
            operator_id=op_user.id, # Use actual op_user.id
            device_binding_id=device_binding.id, # Use actual device_binding.id
            notes=session_notes,
            date=datetime.utcnow()
            # device_task_id can be None or some integer
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        retrieved_session = self.db.query(Session).get(session.id)
        self.assertIsNotNone(retrieved_session)
        self.assertEqual(retrieved_session.notes, session_notes)
        self.assertIsNotNone(retrieved_session.patient)
        self.assertEqual(retrieved_session.patient.full_name, "Session Patient")
        self.assertIsNotNone(retrieved_session.operator)
        self.assertEqual(retrieved_session.operator.username, "operator")
        self.assertIsNotNone(retrieved_session.device_binding)
        self.assertEqual(retrieved_session.device_binding.ip_address, "127.0.0.1")

if __name__ == '__main__':
    unittest.main()

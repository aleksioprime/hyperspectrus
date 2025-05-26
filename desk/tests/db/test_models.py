import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime

# Adjust the import path based on the actual location of your models
from desk.src.db.models import (
    User, Patient, Session, Device, DeviceBinding, Role, Organization, 
    Spectrum, Chromophore, OverlapCoefficient,
    RawImage, ReconstructedImage, Result  # Added RawImage, ReconstructedImage, Result
)

# The db_session fixture is defined in desk/tests/conftest.py

# ==== User Model Tests ====

def test_create_user(db_session):
    user_data = {
        "username": "testuser",
        "hashed_password": "password123",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    retrieved_user = db_session.query(User).filter_by(username="testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.email == user_data["email"]
    assert retrieved_user.full_name == "Test User"
    assert retrieved_user.is_active  # Default value check
    assert not retrieved_user.is_superuser  # Default value check

def test_user_full_name_property(db_session):
    # Case 1: First and last name
    user1 = User(username="user1", hashed_password="pw", email="e1@example.com", first_name="John", last_name="Doe")
    db_session.add(user1)
    db_session.commit()
    assert user1.full_name == "John Doe"

    # Case 2: Only first name
    user2 = User(username="user2", hashed_password="pw", email="e2@example.com", first_name="Jane")
    db_session.add(user2)
    db_session.commit()
    assert user2.full_name == "Jane"

    # Case 3: Only last name
    user3 = User(username="user3", hashed_password="pw", email="e3@example.com", last_name="Smith")
    db_session.add(user3)
    db_session.commit()
    assert user3.full_name == "Smith"

    # Case 4: No first or last name
    user4 = User(username="user4", hashed_password="pw", email="e4@example.com")
    db_session.add(user4)
    db_session.commit()
    assert user4.full_name == ""
    
    # Case 5: First name is None, last name present
    user5 = User(username="user5", hashed_password="pw", email="e5@example.com", first_name=None, last_name="OnlyLast")
    db_session.add(user5)
    db_session.commit()
    assert user5.full_name == "OnlyLast"

    # Case 6: Last name is None, first name present
    user6 = User(username="user6", hashed_password="pw", email="e6@example.com", first_name="OnlyFirst", last_name=None)
    db_session.add(user6)
    db_session.commit()
    assert user6.full_name == "OnlyFirst"

def test_user_username_not_nullable(db_session):
    user_data = {
        "username": None,
        "hashed_password": "password",
        "email": "test_nonull_user@example.com"
    }
    with pytest.raises(IntegrityError):
        u = User(**user_data)
        db_session.add(u)
        db_session.commit()

def test_user_username_unique(db_session):
    user1_data = {"username": "uniqueuser", "hashed_password": "pw1", "email": "email1_unique_user@example.com"}
    user2_data = {"username": "uniqueuser", "hashed_password": "pw2", "email": "email2_unique_user@example.com"}
    
    u1 = User(**user1_data)
    db_session.add(u1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        u2 = User(**user2_data)
        db_session.add(u2)
        db_session.commit()

def test_user_email_not_nullable(db_session):
    user_data = {
        "username": "test_nonull_email",
        "hashed_password": "password",
        "email": None
    }
    with pytest.raises(IntegrityError):
        u = User(**user_data)
        db_session.add(u)
        db_session.commit()

def test_user_email_unique(db_session):
    user1_data = {"username": "user1_unique_email", "hashed_password": "pw1", "email": "unique_email@example.com"}
    user2_data = {"username": "user2_unique_email", "hashed_password": "pw2", "email": "unique_email@example.com"}
    
    u1 = User(**user1_data)
    db_session.add(u1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        u2 = User(**user2_data)
        db_session.add(u2)
        db_session.commit()

def test_user_hashed_password_not_nullable(db_session):
    user_data = {
        "username": "test_nonull_pass",
        "hashed_password": None,
        "email": "test_nonull_pass@example.com"
    }
    with pytest.raises(IntegrityError):
        u = User(**user_data)
        db_session.add(u)
        db_session.commit()

# ==== Patient Model Tests ====

def test_create_patient(db_session):
    patient_data = {
        "full_name": "John Doe",
        "birth_date": date(1990, 1, 1),
        "notes": "Test patient notes"
    }
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    retrieved_patient = db_session.query(Patient).filter_by(full_name="John Doe").first()
    assert retrieved_patient is not None
    assert retrieved_patient.birth_date == patient_data["birth_date"]
    assert retrieved_patient.created_at is not None

def test_patient_full_name_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        p = Patient(full_name=None, birth_date=date(2000, 1, 1))
        db_session.add(p)
        db_session.commit()

def test_patient_birth_date_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        p = Patient(full_name="No Birthdate Patient", birth_date=None)
        db_session.add(p)
        db_session.commit()

# ==== Session Model Tests ====

def test_create_session_with_patient_and_operator(db_session):
    # 1. Create Operator (User)
    op_user = User(
        username="operator",
        hashed_password="op_password",
        email="operator@example.com",
        first_name="Op",
        last_name="Erator"
    )
    db_session.add(op_user)
    db_session.commit()

    # 2. Create Patient
    patient = Patient(
        full_name="Session Patient",
        birth_date=date(1985, 5, 15)
    )
    db_session.add(patient)
    db_session.commit()

    # 3. Create Device and DeviceBinding
    device = Device(name="Test Device for Session")
    db_session.add(device)
    db_session.commit()

    device_binding = DeviceBinding(
        user_id=op_user.id,
        device_id=device.id,
        ip_address="127.0.0.1"
    )
    db_session.add(device_binding)
    db_session.commit()

    # 4. Create Session
    session_notes = "Test session notes"
    session_data = Session(
        patient_id=patient.id,
        operator_id=op_user.id,
        device_binding_id=device_binding.id,
        notes=session_notes,
        date=datetime.utcnow()
    )
    db_session.add(session_data)
    db_session.commit()
    db_session.refresh(session_data)

    retrieved_session = db_session.query(Session).get(session_data.id)
    assert retrieved_session is not None
    assert retrieved_session.notes == session_notes
    assert retrieved_session.patient is not None
    assert retrieved_session.patient.full_name == "Session Patient"
    assert retrieved_session.operator is not None
    assert retrieved_session.operator.username == "operator"
    assert retrieved_session.device_binding is not None
    assert retrieved_session.device_binding.ip_address == "127.0.0.1"
    assert retrieved_session.created_at is not None # Default check for created_at
    assert retrieved_session.updated_at is not None # Default check for updated_at
    assert retrieved_session.date is not None # Ensure date was set
    # Ensure patient_id, operator_id, device_binding_id are correctly set
    assert retrieved_session.patient_id == patient.id
    assert retrieved_session.operator_id == op_user.id
    assert retrieved_session.device_binding_id == device_binding.id
    assert retrieved_session.photos_downloaded is False # Test default value

def test_session_nullable_constraints(db_session):
    user = User(username="session_test_user", hashed_password="pw", email="stu@example.com")
    patient = Patient(full_name="Session Test Patient", birth_date=date(1990,1,1))
    device = Device(name="Session Test Device")
    db_session.add_all([user, patient, device])
    db_session.commit()
    
    device_binding = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="1.1.1.1")
    db_session.add(device_binding)
    db_session.commit()

    # Test patient_id nullable=False
    with pytest.raises(IntegrityError):
        s = Session(patient_id=None, operator_id=user.id, device_binding_id=device_binding.id, date=datetime.utcnow())
        db_session.add(s)
        db_session.commit()
    db_session.rollback()

    # Test operator_id nullable=False
    with pytest.raises(IntegrityError):
        s = Session(patient_id=patient.id, operator_id=None, device_binding_id=device_binding.id, date=datetime.utcnow())
        db_session.add(s)
        db_session.commit()
    db_session.rollback()

    # Test device_binding_id nullable=False
    with pytest.raises(IntegrityError):
        s = Session(patient_id=patient.id, operator_id=user.id, device_binding_id=None, date=datetime.utcnow())
        db_session.add(s)
        db_session.commit()
    db_session.rollback()

def test_session_cascade_delete(db_session):
    # 1. Setup: User, Patient, Device, DeviceBinding, Session
    user = User(username="cascade_user", hashed_password="pw", email="cascade@example.com")
    patient = Patient(full_name="Cascade Patient", birth_date=date(2000, 1, 1))
    device = Device(name="Cascade Device")
    spectrum = Spectrum(wavelength=500) # device relation handled below
    chromophore = Chromophore(name="Cascade Chromo", symbol="CC")
    db_session.add_all([user, patient, device, spectrum, chromophore])
    db_session.commit() # Commit to get IDs

    spectrum.device_id = device.id # Assign after device has ID
    db_session.commit()


    device_binding = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="1.2.3.9")
    db_session.add(device_binding)
    db_session.commit()

    session_obj = Session(
        patient_id=patient.id, 
        operator_id=user.id, 
        device_binding_id=device_binding.id, 
        date=datetime.utcnow()
    )
    db_session.add(session_obj)
    db_session.commit()
    session_id = session_obj.id

    # 2. Add related objects
    raw_image = RawImage(session_id=session_id, spectrum_id=spectrum.id, file_path="/path/raw.img")
    reconstructed_image = ReconstructedImage(session_id=session_id, chromophore_id=chromophore.id, file_path="/path/recon.img")
    result_obj = Result(session_id=session_id, s_coefficient=1.0, mean_lesion_thb=1.0, mean_skin_thb=1.0)
    db_session.add_all([raw_image, reconstructed_image, result_obj])
    db_session.commit()
    
    raw_image_id = raw_image.id
    reconstructed_image_id = reconstructed_image.id
    result_id = result_obj.id

    # Verify they exist
    assert db_session.query(RawImage).get(raw_image_id) is not None
    assert db_session.query(ReconstructedImage).get(reconstructed_image_id) is not None
    assert db_session.query(Result).get(result_id) is not None

    # 3. Delete the Session
    db_session.delete(session_obj)
    db_session.commit()
    
    # 4. Verify related objects are deleted (due to cascade)
    # Need to query again, possibly after expiring all or in a new session context for some DBs
    # For SQLite in-memory with this fixture setup, direct query should reflect changes.
    assert db_session.query(RawImage).get(raw_image_id) is None
    assert db_session.query(ReconstructedImage).get(reconstructed_image_id) is None
    assert db_session.query(Result).get(result_id) is None


# ==== Device Model Tests ====
# test_create_device was already present, enhancing it and adding constraints.
def test_create_device(db_session):
    device = Device(name="Hyperspectral Imager X1000")
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    
    retrieved_device = db_session.query(Device).filter_by(name="Hyperspectral Imager X1000").first()
    assert retrieved_device is not None
    assert retrieved_device.name == "Hyperspectral Imager X1000"
    assert retrieved_device.id is not None
    assert retrieved_device.created_at is not None
    assert retrieved_device.updated_at is not None

def test_device_name_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        d = Device(name=None)
        db_session.add(d)
        db_session.commit()

def test_device_name_unique(db_session):
    device1 = Device(name="UniqueDeviceName")
    db_session.add(device1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        device2 = Device(name="UniqueDeviceName")
        db_session.add(device2)
        db_session.commit()
    db_session.rollback()


# ==== Spectrum Model Tests ====

def test_create_spectrum(db_session):
    device = Device(name="SpectrumDevice")
    db_session.add(device)
    db_session.commit()

    spectrum = Spectrum(wavelength=550, device_id=device.id, rgb_r=120, rgb_g=130, rgb_b=140)
    db_session.add(spectrum)
    db_session.commit()
    db_session.refresh(spectrum)

    retrieved_spectrum = db_session.query(Spectrum).filter_by(wavelength=550).first()
    assert retrieved_spectrum is not None
    assert retrieved_spectrum.wavelength == 550
    assert retrieved_spectrum.device_id == device.id
    assert retrieved_spectrum.rgb_r == 120
    assert retrieved_spectrum.rgb_g == 130
    assert retrieved_spectrum.rgb_b == 140
    assert retrieved_spectrum.id is not None

def test_spectrum_wavelength_not_nullable(db_session):
    device = Device(name="SpecDeviceWL")
    db_session.add(device)
    db_session.commit()
    with pytest.raises(IntegrityError):
        s = Spectrum(wavelength=None, device_id=device.id)
        db_session.add(s)
        db_session.commit()

def test_spectrum_device_id_not_nullable(db_session):
    # Testing device_id nullable=False implicitly by not providing device_id
    with pytest.raises(IntegrityError):
        s = Spectrum(wavelength=600) # device_id is None
        db_session.add(s)
        db_session.commit()

def test_spectrum_device_id_fk_constraint(db_session):
    # Attempt to create spectrum with a non-existent device_id
    with pytest.raises(IntegrityError): # SQLAlchemy typically raises IntegrityError for FK violations
        s = Spectrum(wavelength=600, device_id=99999) # Assuming 99999 does not exist
        db_session.add(s)
        db_session.commit()

def test_spectrum_device_relationship(db_session):
    device = Device(name="DeviceForSpectrumRel")
    db_session.add(device)
    db_session.commit()

    s1 = Spectrum(wavelength=500, device_id=device.id)
    s2 = Spectrum(wavelength=510, device=device) # Test assigning object directly
    db_session.add_all([s1, s2])
    db_session.commit()
    db_session.refresh(device)
    db_session.refresh(s1)
    db_session.refresh(s2)

    assert s1.device == device
    assert s2.device == device
    assert len(device.spectra) == 2
    assert s1 in device.spectra
    assert s2 in device.spectra


# ==== Chromophore Model Tests ====

def test_create_chromophore(db_session):
    chromo = Chromophore(name="Oxyhemoglobin", symbol="HbO2", type="Blood")
    db_session.add(chromo)
    db_session.commit()
    db_session.refresh(chromo)

    retrieved_chromo = db_session.query(Chromophore).filter_by(name="Oxyhemoglobin").first()
    assert retrieved_chromo is not None
    assert retrieved_chromo.symbol == "HbO2"
    assert retrieved_chromo.type == "Blood"
    assert retrieved_chromo.id is not None

def test_chromophore_name_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        c = Chromophore(name=None, symbol="Test", type="Test")
        db_session.add(c)
        db_session.commit()

def test_chromophore_name_unique(db_session):
    c1 = Chromophore(name="UniqueChromoName", symbol="UCN", type="Test")
    db_session.add(c1)
    db_session.commit()
    with pytest.raises(IntegrityError):
        c2 = Chromophore(name="UniqueChromoName", symbol="UCN2", type="Test")
        db_session.add(c2)
        db_session.commit()
    db_session.rollback()

def test_chromophore_symbol_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        c = Chromophore(name="TestSymbol", symbol=None, type="Test")
        db_session.add(c)
        db_session.commit()

def test_chromophore_symbol_unique(db_session):
    c1 = Chromophore(name="ChromoSymbol1", symbol="UCS", type="Test")
    db_session.add(c1)
    db_session.commit()
    with pytest.raises(IntegrityError):
        c2 = Chromophore(name="ChromoSymbol2", symbol="UCS", type="Test")
        db_session.add(c2)
        db_session.commit()
    db_session.rollback()


# ==== OverlapCoefficient Model Tests ====

def test_create_overlap_coefficient(db_session):
    device = Device(name="OverlapDevice")
    spectrum = Spectrum(wavelength=700, device=device)
    chromophore = Chromophore(name="Melanin", symbol="Mel", type="Pigment")
    db_session.add_all([device, spectrum, chromophore])
    db_session.commit()

    overlap = OverlapCoefficient(
        spectrum_id=spectrum.id, 
        chromophore_id=chromophore.id, 
        coefficient=0.75
    )
    db_session.add(overlap)
    db_session.commit()
    db_session.refresh(overlap)

    retrieved_overlap = db_session.query(OverlapCoefficient).first()
    assert retrieved_overlap is not None
    assert retrieved_overlap.spectrum_id == spectrum.id
    assert retrieved_overlap.chromophore_id == chromophore.id
    assert retrieved_overlap.coefficient == 0.75
    assert retrieved_overlap.id is not None

def test_overlap_spectrum_id_not_nullable(db_session):
    chromophore = Chromophore(name="OverlapChromo1", symbol="OC1", type="Test")
    db_session.add(chromophore)
    db_session.commit()
    with pytest.raises(IntegrityError):
        ov = OverlapCoefficient(spectrum_id=None, chromophore_id=chromophore.id, coefficient=0.5)
        db_session.add(ov)
        db_session.commit()

def test_overlap_chromophore_id_not_nullable(db_session):
    device = Device(name="OverlapDevice2")
    spectrum = Spectrum(wavelength=710, device=device)
    db_session.add_all([device, spectrum])
    db_session.commit()
    with pytest.raises(IntegrityError):
        ov = OverlapCoefficient(spectrum_id=spectrum.id, chromophore_id=None, coefficient=0.5)
        db_session.add(ov)
        db_session.commit()

def test_overlap_coefficient_value_not_nullable(db_session):
    device = Device(name="OverlapDevice3")
    spectrum = Spectrum(wavelength=720, device=device)
    chromophore = Chromophore(name="OverlapChromo2", symbol="OC2", type="Test")
    db_session.add_all([device, spectrum, chromophore])
    db_session.commit()
    with pytest.raises(IntegrityError):
        ov = OverlapCoefficient(spectrum_id=spectrum.id, chromophore_id=chromophore.id, coefficient=None)
        db_session.add(ov)
        db_session.commit()

def test_overlap_relationships(db_session):
    device = Device(name="OverlapRelDevice")
    spectrum = Spectrum(wavelength=750, device=device)
    chromophore = Chromophore(name="TestChromoRel", symbol="TCR", type="Test")
    db_session.add_all([device, spectrum, chromophore])
    db_session.commit()

    overlap = OverlapCoefficient(spectrum=spectrum, chromophore=chromophore, coefficient=0.8)
    db_session.add(overlap)
    db_session.commit()
    db_session.refresh(spectrum)
    db_session.refresh(chromophore)
    db_session.refresh(overlap)

    assert overlap.spectrum == spectrum
    assert overlap.chromophore == chromophore
    assert overlap in spectrum.overlaps
    assert overlap in chromophore.overlaps


def test_create_device_binding_constraints(db_session):
    # Test unique constraint for (user_id, device_id) - if it exists
    # Test foreign key constraints by trying to bind to non-existent user/device
    
    # 1. Create User and Device
    user = User(username="binder_user", hashed_password="pw", email="binder@example.com")
    device = Device(name="Bindable Device")
    db_session.add_all([user, device])
    db_session.commit()

    # 2. Create a valid binding
    binding1 = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="192.168.1.100")
    db_session.add(binding1)
    db_session.commit()
    
    retrieved_binding = db_session.query(DeviceBinding).first()
    assert retrieved_binding is not None
    assert retrieved_binding.ip_address == "192.168.1.100"

    # Test non-nullable ip_address
    with pytest.raises(IntegrityError):
        binding_no_ip = DeviceBinding(user_id=user.id, device_id=device.id, ip_address=None)
        db_session.add(binding_no_ip)
        db_session.commit()
    db_session.rollback() # Important to rollback after expected error for subsequent tests

    # Test foreign key for user_id
    with pytest.raises(IntegrityError): # Or the specific error SQLAlchemy raises for FK violation
        binding_bad_user = DeviceBinding(user_id=9999, device_id=device.id, ip_address="1.2.3.4")
        db_session.add(binding_bad_user)
        db_session.commit()
    db_session.rollback()

    # Test foreign key for device_id
    with pytest.raises(IntegrityError):
        binding_bad_device = DeviceBinding(user_id=user.id, device_id=9999, ip_address="1.2.3.5")
        db_session.add(binding_bad_device)
        db_session.commit()
    db_session.rollback()
    
    # Test unique constraint on (user_id, device_id) if your model has one
    # (Assuming UniqueConstraint('user_id', 'device_id', name='uq_user_device') is defined in model)
    # With the current models.py, this constraint is not explicitly defined.
    # If it were, this test would be:
    # with pytest.raises(IntegrityError):
    #     binding_duplicate = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="192.168.1.101")
    #     db_session.add(binding_duplicate)
    #     db_session.commit()
    # db_session.rollback()

def test_device_binding_relationships(db_session):
    user = User(username="db_user_rel", hashed_password="pw", email="db_user_rel@example.com")
    device = Device(name="DB Device Rel")
    db_session.add_all([user, device])
    db_session.commit()

    binding = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="10.0.0.1")
    db_session.add(binding)
    db_session.commit()
    db_session.refresh(binding)
    db_session.refresh(user) # Refresh to see backrefs if they exist
    db_session.refresh(device) # Refresh to see backrefs if they exist

    assert binding.user == user
    assert binding.device == device
    
    # Test backreferences if defined in User and Device models
    # e.g., if User has user.device_bindings = relationship("DeviceBinding", back_populates="user")
    if hasattr(user, 'device_bindings'):
         assert binding in user.device_bindings
    # e.g., if Device has device.device_bindings = relationship("DeviceBinding", back_populates="device")
    if hasattr(device, 'device_bindings'):
         assert binding in device.device_bindings

# Note: The current DeviceBinding model provided does not explicitly define unique constraints
# for (user_id, device_id) or for ip_address. The FKs and nullable=False for ip_address are tested.

# Test default values for created_at and updated_at in general (can be part of any model test)
def test_default_timestamps(db_session):
    user = User(username="timestamp_user", hashed_password="pw", email="ts@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.created_at is not None
    assert user.updated_at is not None
    first_updated_at = user.updated_at
    
    # Check if updated_at changes on modification
    user.email = "ts_updated@example.com"
    db_session.commit()
    db_session.refresh(user)
    assert user.updated_at is not None
    assert user.updated_at > first_updated_at

    # For models with onupdate=datetime.utcnow for updated_at
    # This is typically handled by SQLAlchemy's event system or default functions.
    # The default Column(..., default=datetime.utcnow, onupdate=datetime.utcnow) should work.
    # If you want to be very precise about the onupdate behavior vs default:
    # 1. Create object, commit -> created_at and updated_at are set.
    # 2. Modify object, commit -> updated_at should change, created_at should not.
    patient = Patient(full_name="Timestamp Patient", birth_date=date(2000,1,1))
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    assert patient.created_at is not None
    assert patient.updated_at is not None
    patient_created_at = patient.created_at
    patient_first_updated_at = patient.updated_at

    patient.notes = "Adding a note to trigger update."
    db_session.commit()
    db_session.refresh(patient)
    assert patient.updated_at > patient_first_updated_at
    assert patient.created_at == patient_created_at


# ==== Role Model Tests ====

def test_create_role(db_session):
    role = Role(name="Administrator")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    
    retrieved_role = db_session.query(Role).filter_by(name="Administrator").first()
    assert retrieved_role is not None
    assert retrieved_role.name == "Administrator"
    assert retrieved_role.id is not None

def test_role_name_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        r = Role(name=None)
        db_session.add(r)
        db_session.commit()

def test_role_name_unique(db_session):
    role1 = Role(name="Editor")
    db_session.add(role1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        role2 = Role(name="Editor")
        db_session.add(role2)
        db_session.commit()
    db_session.rollback()

def test_role_user_relationship(db_session):
    user = User(username="role_user", hashed_password="pw", email="role_user@example.com")
    role = Role(name="Contributor")
    db_session.add_all([user, role])
    db_session.commit()

    user.roles.append(role)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(role)

    assert role in user.roles
    assert user in role.users
    retrieved_user = db_session.query(User).filter_by(username="role_user").first()
    assert len(retrieved_user.roles) == 1
    assert retrieved_user.roles[0].name == "Contributor"


# ==== Organization Model Tests ====

def test_create_organization(db_session):
    org = Organization(name="HyperCorp")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    retrieved_org = db_session.query(Organization).filter_by(name="HyperCorp").first()
    assert retrieved_org is not None
    assert retrieved_org.name == "HyperCorp"
    assert retrieved_org.id is not None

def test_organization_name_not_nullable(db_session):
    with pytest.raises(IntegrityError):
        org = Organization(name=None)
        db_session.add(org)
        db_session.commit()

def test_organization_name_unique(db_session):
    org1 = Organization(name="UniqueOrg")
    db_session.add(org1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        org2 = Organization(name="UniqueOrg")
        db_session.add(org2)
        db_session.commit()
    db_session.rollback()

def test_organization_user_patient_relationship(db_session):
    org = Organization(name="TestClinic")
    user = User(username="org_user", hashed_password="pw", email="org_user@example.com")
    patient = Patient(full_name="Org Patient", birth_date=date(1995, 6, 10))
    
    db_session.add_all([org, user, patient])
    db_session.commit() # Commit org first to get ID if not using explicit assignment below

    # Assign organization
    user.organization_id = org.id
    patient.organization_id = org.id 
    # Or:
    # user.organization = org
    # patient.organization = org
    
    db_session.commit()
    db_session.refresh(org)
    db_session.refresh(user)
    db_session.refresh(patient)

    assert user in org.users
    assert patient in org.patients
    assert user.organization == org
    assert patient.organization == org
    
    retrieved_org = db_session.query(Organization).filter_by(name="TestClinic").first()
    assert len(retrieved_org.users) == 1
    assert retrieved_org.users[0].username == "org_user"
    assert len(retrieved_org.patients) == 1
    assert retrieved_org.patients[0].full_name == "Org Patient"


# ==== RawImage Model Tests ====

def test_create_raw_image(db_session):
    user = User(username="raw_user", hashed_password="pw", email="raw@example.com")
    patient = Patient(full_name="Raw Patient", birth_date=date(2001,1,1))
    device = Device(name="Raw Device")
    db_session.add_all([user, patient, device])
    db_session.commit()

    spectrum = Spectrum(wavelength=450, device_id=device.id)
    db_session.add(spectrum)
    db_session.commit()
    
    device_binding = DeviceBinding(user_id=user.id, device_id=device.id, ip_address="1.2.3.10")
    db_session.add(device_binding)
    db_session.commit()

    session_obj = Session(patient_id=patient.id, operator_id=user.id, device_binding_id=device_binding.id, date=datetime.utcnow())
    db_session.add(session_obj)
    db_session.commit()

    raw_image = RawImage(session_id=session_obj.id, spectrum_id=spectrum.id, file_path="/path/to/raw.png")
    db_session.add(raw_image)
    db_session.commit()
    db_session.refresh(raw_image)

    assert raw_image.id is not None
    assert raw_image.file_path == "/path/to/raw.png"
    assert raw_image.session_id == session_obj.id
    assert raw_image.spectrum_id == spectrum.id

def test_raw_image_nullable_constraints(db_session):
    user, patient, device, spectrum, session_obj = _setup_for_image_tests(db_session, "raw_nullable")

    with pytest.raises(IntegrityError):
        ri = RawImage(session_id=None, spectrum_id=spectrum.id, file_path="/path/raw_s_null.img")
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError):
        ri = RawImage(session_id=session_obj.id, spectrum_id=None, file_path="/path/raw_spec_null.img")
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()
    
    with pytest.raises(IntegrityError):
        ri = RawImage(session_id=session_obj.id, spectrum_id=spectrum.id, file_path=None)
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()

def test_raw_image_relationships(db_session):
    user, patient, device, spectrum, session_obj = _setup_for_image_tests(db_session, "raw_rel")
    
    raw_image = RawImage(session_id=session_obj.id, spectrum_id=spectrum.id, file_path="/path/raw_rel.img")
    db_session.add(raw_image)
    db_session.commit()
    db_session.refresh(raw_image)
    db_session.refresh(session_obj)
    db_session.refresh(spectrum)

    assert raw_image.session == session_obj
    assert raw_image.spectrum == spectrum
    assert raw_image in session_obj.raw_images
    assert raw_image in spectrum.raw_images


# ==== ReconstructedImage Model Tests ====

def test_create_reconstructed_image(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "recon_create") # Spectrum not needed directly
    chromophore = Chromophore(name="ReconChromo", symbol="RC", type="Test")
    db_session.add(chromophore)
    db_session.commit()

    recon_image = ReconstructedImage(session_id=session_obj.id, chromophore_id=chromophore.id, file_path="/path/to/recon.png")
    db_session.add(recon_image)
    db_session.commit()
    db_session.refresh(recon_image)

    assert recon_image.id is not None
    assert recon_image.file_path == "/path/to/recon.png"
    assert recon_image.session_id == session_obj.id
    assert recon_image.chromophore_id == chromophore.id

def test_reconstructed_image_nullable_constraints(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "recon_nullable")
    chromophore = Chromophore(name="ReconChromoNull", symbol="RCN", type="Test")
    db_session.add(chromophore)
    db_session.commit()

    with pytest.raises(IntegrityError):
        ri = ReconstructedImage(session_id=None, chromophore_id=chromophore.id, file_path="/path/recon_s_null.img")
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError):
        ri = ReconstructedImage(session_id=session_obj.id, chromophore_id=None, file_path="/path/recon_c_null.img")
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()
    
    with pytest.raises(IntegrityError):
        ri = ReconstructedImage(session_id=session_obj.id, chromophore_id=chromophore.id, file_path=None)
        db_session.add(ri)
        db_session.commit()
    db_session.rollback()

def test_reconstructed_image_relationships(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "recon_rel")
    chromophore = Chromophore(name="ReconChromoRel", symbol="RCR", type="Test")
    db_session.add(chromophore)
    db_session.commit()
    
    recon_image = ReconstructedImage(session_id=session_obj.id, chromophore_id=chromophore.id, file_path="/path/recon_rel.img")
    db_session.add(recon_image)
    db_session.commit()
    db_session.refresh(recon_image)
    db_session.refresh(session_obj)
    db_session.refresh(chromophore)

    assert recon_image.session == session_obj
    assert recon_image.chromophore == chromophore
    assert recon_image in session_obj.reconstructed_images
    assert recon_image in chromophore.reconstructed_images


# ==== Result Model Tests ====

def test_create_result(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "result_create")

    result = Result(
        session_id=session_obj.id, 
        s_coefficient=1.23, 
        mean_lesion_thb=45.6, 
        mean_skin_thb=78.9,
        contour_path="/path/contour.dat",
        thb_path="/path/thb.dat"
    )
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)

    assert result.id is not None
    assert result.session_id == session_obj.id
    assert result.s_coefficient == 1.23
    assert result.mean_lesion_thb == 45.6
    assert result.mean_skin_thb == 78.9
    assert result.contour_path == "/path/contour.dat" # Can be None
    assert result.thb_path == "/path/thb.dat" # Can be None


def test_result_nullable_constraints(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "result_nullable")

    with pytest.raises(IntegrityError): # session_id
        res = Result(session_id=None, s_coefficient=1.0, mean_lesion_thb=1.0, mean_skin_thb=1.0)
        db_session.add(res)
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError): # s_coefficient
        res = Result(session_id=session_obj.id, s_coefficient=None, mean_lesion_thb=1.0, mean_skin_thb=1.0)
        db_session.add(res)
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError): # mean_lesion_thb
        res = Result(session_id=session_obj.id, s_coefficient=1.0, mean_lesion_thb=None, mean_skin_thb=1.0)
        db_session.add(res)
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError): # mean_skin_thb
        res = Result(session_id=session_obj.id, s_coefficient=1.0, mean_lesion_thb=1.0, mean_skin_thb=None)
        db_session.add(res)
        db_session.commit()
    db_session.rollback()

def test_result_session_id_unique(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "result_unique")
    
    res1 = Result(session_id=session_obj.id, s_coefficient=1.0, mean_lesion_thb=1.0, mean_skin_thb=1.0)
    db_session.add(res1)
    db_session.commit()

    with pytest.raises(IntegrityError):
        res2 = Result(session_id=session_obj.id, s_coefficient=2.0, mean_lesion_thb=2.0, mean_skin_thb=2.0)
        db_session.add(res2)
        db_session.commit()
    db_session.rollback()

def test_result_session_relationship(db_session):
    user, patient, device, _, session_obj = _setup_for_image_tests(db_session, "result_rel")
    
    result = Result(session_id=session_obj.id, s_coefficient=1.5, mean_lesion_thb=50.0, mean_skin_thb=80.0)
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)
    db_session.refresh(session_obj)

    assert result.session == session_obj
    assert session_obj.result == result # Assuming one-to-one


# Helper function for setting up common entities for image/result tests
def _setup_for_image_tests(db_session, prefix: str):
    user = User(username=f"{prefix}_user", hashed_password="pw", email=f"{prefix}@example.com")
    patient = Patient(full_name=f"{prefix} Patient", birth_date=date(2002,1,1))
    device = Device(name=f"{prefix} Device")
    db_session.add_all([user, patient, device])
    db_session.commit()

    spectrum = Spectrum(wavelength=450 + hash(prefix) % 100, device_id=device.id) # Vary wavelength
    db_session.add(spectrum)
    db_session.commit()
    
    device_binding = DeviceBinding(user_id=user.id, device_id=device.id, ip_address=f"1.2.3.{hash(prefix)%255}")
    db_session.add(device_binding)
    db_session.commit()

    session_obj = Session(patient_id=patient.id, operator_id=user.id, device_binding_id=device_binding.id, date=datetime.utcnow())
    db_session.add(session_obj)
    db_session.commit()
    return user, patient, device, spectrum, session_obj

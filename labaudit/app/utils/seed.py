"""
Seed script - demo data for Nexus Food Analytics Sdn Bhd
"""
import logging
import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Organization, User, UserRole,
    Document, DocumentType, DocumentStatus, ComplianceCategory,
    CalibrationRecord, CalibrationStatus,
    TrainingRecord, TrainingType, TrainingStatus,
    CapaItem, CapaType, CapaPriority, CapaStatus,
)

logger = logging.getLogger(__name__)
TODAY = date.today()


def _d(offset: int) -> date:
    return TODAY + timedelta(days=offset)


def _hash(plain: str) -> str:
    """Simple bcrypt hash - compatible with all bcrypt versions."""
    import bcrypt as _bcrypt
    # Fix for bcrypt 4.x
    if not hasattr(_bcrypt, '__about__'):
        _bcrypt.__about__ = type('a', (), {'__version__': _bcrypt.__version__})()
    pw = plain.encode("utf-8")
    if len(pw) > 72:
        pw = pw[:72]
    return _bcrypt.hashpw(pw, _bcrypt.gensalt()).decode("utf-8")


def seed_organization(db: Session) -> Organization:
    existing = db.query(Organization).filter_by(slug="nexus-food-analytics").first()
    if existing:
        return existing
    org = Organization(
        id=uuid.uuid4(),
        name="Nexus Food Analytics Sdn Bhd",
        slug="nexus-food-analytics",
        industry="food_testing",
        address="No. 12, Jalan Teknologi 3, Petaling Jaya, Selangor",
        contact_email="quality@nexusfood.com.my",
        is_active=True,
    )
    db.add(org)
    db.flush()
    return org


def seed_users(db: Session, org: Organization) -> dict[str, User]:
    users_data = [
        {"email": "admin@nexusfood.com.my",             "full_name": "Dr. Amirah Zulkifli",    "job_title": "Laboratory Director",  "department": "Management",        "role": UserRole.ADMIN,   "password": "Admin1234"},
        {"email": "quality.manager@nexusfood.com.my",   "full_name": "Hafizuddin Ramli",        "job_title": "Quality Manager",      "department": "Quality Assurance", "role": UserRole.MANAGER, "password": "Manager1234"},
        {"email": "compliance@nexusfood.com.my",        "full_name": "Nurul Ain Ibrahim",       "job_title": "Compliance Officer",   "department": "Quality Assurance", "role": UserRole.MANAGER, "password": "Manager1234"},
        {"email": "lab.microbio@nexusfood.com.my",      "full_name": "Tan Wei Liang",           "job_title": "Senior Microbiologist","department": "Microbiology",      "role": UserRole.VIEWER,  "password": "Viewer1234"},
        {"email": "lab.chem@nexusfood.com.my",          "full_name": "Priya Krishnamoorthy",    "job_title": "Analytical Chemist",   "department": "Chemistry",         "role": UserRole.VIEWER,  "password": "Viewer1234"},
        {"email": "lab.tech@nexusfood.com.my",          "full_name": "Muhammad Faizal Othman",  "job_title": "Lab Technician",       "department": "Microbiology",      "role": UserRole.VIEWER,  "password": "Viewer1234"},
    ]
    created = {}
    for data in users_data:
        existing = db.query(User).filter_by(email=data["email"]).first()
        if existing:
            created[data["email"]] = existing
            continue
        user = User(
            id=uuid.uuid4(),
            org_id=org.id,
            email=data["email"],
            hashed_password=_hash(data["password"]),
            full_name=data["full_name"],
            job_title=data["job_title"],
            department=data["department"],
            role=data["role"],
            is_active=True,
        )
        db.add(user)
        created[data["email"]] = user
    db.flush()
    logger.info("Seeded %d users", len(created))
    return created


def seed_documents(db: Session, org: Organization, users: dict) -> None:
    manager  = users["quality.manager@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]
    chemist  = users["lab.chem@nexusfood.com.my"]
    microbio = users["lab.microbio@nexusfood.com.my"]

    docs = [
        ("SOP for Microbial Enumeration by Pour Plate Method", "SOP-MB-001", DocumentType.SOP, ComplianceCategory.ISO_17025, "Microbiology", 3, DocumentStatus.ACTIVE, _d(180), microbio),
        ("SOP for Total Coliform Detection by MPN Method", "SOP-MB-002", DocumentType.SOP, ComplianceCategory.ISO_17025, "Microbiology", 2, DocumentStatus.ACTIVE, _d(90), microbio),
        ("SOP for Heavy Metal Analysis by ICP-MS", "SOP-CH-001", DocumentType.SOP, ComplianceCategory.ISO_17025, "Chemistry", 4, DocumentStatus.ACTIVE, _d(210), chemist),
        ("SOP for Pesticide Residue Screening by GC-MS", "SOP-CH-002", DocumentType.SOP, ComplianceCategory.ISO_17025, "Chemistry", 2, DocumentStatus.ACTIVE, _d(45), chemist),
        ("SOP for Sample Receipt and Registration", "SOP-QA-001", DocumentType.SOP, ComplianceCategory.ISO_17025, "Quality Assurance", 5, DocumentStatus.ACTIVE, _d(300), manager),
        ("SOP for Internal Audit Procedure", "SOP-QA-002", DocumentType.SOP, ComplianceCategory.ISO_9001, "Quality Assurance", 2, DocumentStatus.ACTIVE, _d(240), compliance),
        ("Quality Manual Rev 7", "QM-001", DocumentType.POLICY, ComplianceCategory.ISO_17025, "Quality Assurance", 7, DocumentStatus.EXPIRING_SOON, _d(12), manager),
        ("SOP for Autoclave Operation and Validation", "SOP-MB-005", DocumentType.SOP, ComplianceCategory.ISO_17025, "Microbiology", 2, DocumentStatus.EXPIRING_SOON, _d(25), microbio),
        ("SOP for Calibration of Analytical Balances", "SOP-EQ-003", DocumentType.SOP, ComplianceCategory.ISO_17025, "Chemistry", 1, DocumentStatus.EXPIRING_SOON, _d(6), chemist),
        ("SOP for Aflatoxin Detection by HPLC", "SOP-CH-008", DocumentType.SOP, ComplianceCategory.ISO_17025, "Chemistry", 2, DocumentStatus.EXPIRED, _d(-15), chemist),
        ("Laboratory Safety Policy", "POL-HSE-001", DocumentType.POLICY, ComplianceCategory.OSHA, "Management", 4, DocumentStatus.EXPIRED, _d(-32), compliance),
        ("Method Validation Protocol Listeria", "MVP-MB-002", DocumentType.SOP, ComplianceCategory.ISO_17025, "Microbiology", 1, DocumentStatus.EXPIRED, _d(-8), microbio),
        ("SOP for Environmental Monitoring Programme", "SOP-MB-010", DocumentType.SOP, ComplianceCategory.ISO_17025, "Microbiology", 1, DocumentStatus.DRAFT, None, microbio),
        ("Data Integrity Policy", "POL-QA-005", DocumentType.POLICY, ComplianceCategory.GMP, "Quality Assurance", 1, DocumentStatus.DRAFT, None, compliance),
    ]
    for title, doc_no, dtype, cat, dept, ver, status, expiry, owner in docs:
        if db.query(Document).filter_by(org_id=org.id, doc_number=doc_no).first():
            continue
        doc = Document(
            id=uuid.uuid4(), org_id=org.id, owner_id=owner.id,
            title=title, doc_number=doc_no, doc_type=dtype,
            compliance_category=cat, department=dept,
            version=ver, is_latest=True, status=status,
            expiry_date=expiry,
            effective_date=_d(-180) if status != DocumentStatus.DRAFT else None,
            file_type="pdf",
        )
        db.add(doc)
    db.flush()
    logger.info("Seeded documents")


def seed_calibration(db: Session, org: Organization, users: dict) -> None:
    chemist = users["lab.chem@nexusfood.com.my"]
    manager = users["quality.manager@nexusfood.com.my"]

    cals = [
        ("Analytical Balance A&D GH-252", "EQ-BAL-001", "Chemistry", _d(-30), _d(335), CalibrationStatus.CURRENT, chemist),
        ("Analytical Balance Mettler Toledo MS204S", "EQ-BAL-002", "Chemistry", _d(-60), _d(305), CalibrationStatus.CURRENT, chemist),
        ("pH Meter Mettler Toledo S210", "EQ-PH-001", "Chemistry", _d(-15), _d(350), CalibrationStatus.CURRENT, chemist),
        ("Autoclave Tuttnauer 2540E", "EQ-AUT-001", "Microbiology", _d(-45), _d(320), CalibrationStatus.CURRENT, manager),
        ("Incubator Memmert IN55", "EQ-INC-001", "Microbiology", _d(-20), _d(345), CalibrationStatus.CURRENT, manager),
        ("HPLC Agilent 1260 Infinity II", "EQ-HPLC-001", "Chemistry", _d(-90), _d(275), CalibrationStatus.CURRENT, chemist),
        ("ICP-MS Agilent 7900", "EQ-ICP-001", "Chemistry", _d(-10), _d(355), CalibrationStatus.CURRENT, chemist),
        ("GC-MS Shimadzu GCMS-TQ8050", "EQ-GCMS-001", "Chemistry", _d(-330), _d(22), CalibrationStatus.DUE_SOON, chemist),
        ("Pipette Calibration Set Class A", "EQ-PIP-001", "Quality Assurance", _d(-340), _d(18), CalibrationStatus.DUE_SOON, manager),
        ("Refrigerator Thermometer Logger", "EQ-LOG-001", "Microbiology", _d(-355), _d(10), CalibrationStatus.DUE_SOON, manager),
        ("Spectrophotometer UV-Vis Shimadzu UV-1900", "EQ-SPEC-001", "Chemistry", _d(-400), _d(-35), CalibrationStatus.OVERDUE, chemist),
        ("Thermometer Reference NIST", "EQ-TEMP-001", "Quality Assurance", _d(-410), _d(-5), CalibrationStatus.OVERDUE, manager),
    ]
    for name, eq_id, dept, last_cal, next_due, status, assignee in cals:
        if db.query(CalibrationRecord).filter_by(org_id=org.id, equipment_id=eq_id).first():
            continue
        db.add(CalibrationRecord(
            id=uuid.uuid4(), org_id=org.id, assigned_to=assignee.id,
            equipment_name=name, equipment_id=eq_id, department=dept,
            last_calibrated=last_cal, next_due=next_due,
            calibration_interval_days=365, status=status,
            calibrated_by="SIRIM QAS International",
        ))
    db.flush()
    logger.info("Seeded calibrations")


def seed_training(db: Session, org: Organization, users: dict) -> None:
    microbio   = users["lab.microbio@nexusfood.com.my"]
    chemist    = users["lab.chem@nexusfood.com.my"]
    manager    = users["quality.manager@nexusfood.com.my"]
    tech       = users["lab.tech@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]

    trainings = [
        (microbio,   "ISO 17025 Awareness Training",          TrainingType.QUALITY_SYSTEMS, _d(-180), _d(185),  TrainingStatus.CURRENT),
        (chemist,    "ISO 17025 Awareness Training",          TrainingType.QUALITY_SYSTEMS, _d(-180), _d(185),  TrainingStatus.CURRENT),
        (manager,    "Internal Auditor Course ISO 17025",     TrainingType.QUALITY_SYSTEMS, _d(-90),  _d(275),  TrainingStatus.CURRENT),
        (compliance, "CAPA Management Best Practices",        TrainingType.REGULATORY,      _d(-60),  _d(305),  TrainingStatus.CURRENT),
        (microbio,   "Biosafety Level 2 Laboratory Practices",TrainingType.SAFETY,          _d(-200), _d(165),  TrainingStatus.CURRENT),
        (tech,       "Good Laboratory Practices Foundation",  TrainingType.QUALITY_SYSTEMS, _d(-30),  _d(335),  TrainingStatus.CURRENT),
        (chemist,    "ICP-MS Operation Agilent 7900",         TrainingType.EQUIPMENT,       _d(-15),  _d(350),  TrainingStatus.CURRENT),
        (tech,       "Chemical Safety and COSHH Awareness",   TrainingType.SAFETY,          _d(-340), _d(25),   TrainingStatus.DUE_SOON),
        (microbio,   "Proficiency Testing PT Scheme",         TrainingType.REGULATORY,      _d(-350), _d(15),   TrainingStatus.DUE_SOON),
        (chemist,    "Laboratory Safety Refresher",           TrainingType.SAFETY,          _d(-355), _d(10),   TrainingStatus.DUE_SOON),
        (tech,       "ISO 17025 Awareness Renewal",          TrainingType.QUALITY_SYSTEMS, _d(-400), _d(-35),  TrainingStatus.OVERDUE),
        (manager,    "Emergency Response and First Aid",      TrainingType.SAFETY,          _d(-420), _d(-55),  TrainingStatus.OVERDUE),
        (compliance, "MS ISO IEC 17025 Lead Assessor",       TrainingType.EXTERNAL_COURSE, _d(-500), None,     TrainingStatus.COMPLETED),
    ]
    for user, title, ttype, completed, expiry, status in trainings:
        if db.query(TrainingRecord).filter_by(org_id=org.id, user_id=user.id, training_title=title).first():
            continue
        db.add(TrainingRecord(
            id=uuid.uuid4(), org_id=org.id, user_id=user.id,
            training_title=title, training_type=ttype,
            completed_date=completed, expiry_date=expiry, status=status,
        ))
    db.flush()
    logger.info("Seeded training records")


def seed_capa(db: Session, org: Organization, users: dict) -> None:
    manager    = users["quality.manager@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]
    chemist    = users["lab.chem@nexusfood.com.my"]
    microbio   = users["lab.microbio@nexusfood.com.my"]

    capas = [
        ("CAPA-2024-001", "Expired SOPs not flagged during monthly document review", CapaType.CORRECTIVE, CapaPriority.HIGH, "Quality Assurance", CapaStatus.CLOSED, _d(-120), _d(-60), _d(-65), compliance, manager),
        ("CAPA-2024-002", "Calibration certificate for HPLC not renewed within grace period", CapaType.CORRECTIVE, CapaPriority.CRITICAL, "Chemistry", CapaStatus.CLOSED, _d(-90), _d(-45), _d(-48), manager, chemist),
        ("CAPA-2024-003", "Technician performed testing without valid competency record", CapaType.CORRECTIVE, CapaPriority.HIGH, "Microbiology", CapaStatus.IN_PROGRESS, _d(-45), _d(15), None, manager, microbio),
        ("CAPA-2024-004", "Temperature excursion in sample storage refrigerator REF-03", CapaType.CORRECTIVE, CapaPriority.CRITICAL, "Microbiology", CapaStatus.IN_PROGRESS, _d(-30), _d(30), None, compliance, manager),
        ("CAPA-2024-005", "Preventive review of proficiency testing performance", CapaType.PREVENTIVE, CapaPriority.MEDIUM, "Chemistry", CapaStatus.OPEN, _d(-20), _d(40), None, manager, chemist),
        ("CAPA-2024-006", "SOP for pesticide residue screening requires update for LC-MS method", CapaType.IMPROVEMENT, CapaPriority.MEDIUM, "Chemistry", CapaStatus.OPEN, _d(-10), _d(50), None, chemist, manager),
        ("CAPA-2024-007", "Laboratory Safety Policy overdue for renewal 32 days past expiry", CapaType.CORRECTIVE, CapaPriority.HIGH, "Management", CapaStatus.OVERDUE, _d(-20), _d(-5), None, compliance, manager),
    ]
    for ref, title, ctype, priority, dept, status, raised, due, closed, raised_by, assigned in capas:
        if db.query(CapaItem).filter_by(org_id=org.id, reference_no=ref).first():
            continue
        db.add(CapaItem(
            id=uuid.uuid4(), org_id=org.id,
            reference_no=ref, title=title, capa_type=ctype,
            priority=priority, department=dept, status=status,
            raised_date=raised, due_date=due, closed_date=closed,
            raised_by=raised_by.id, assigned_to=assigned.id,
        ))
    db.flush()
    logger.info("Seeded CAPA items")


def run_seed(db: Session | None = None) -> None:
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True
    try:
        logger.info("Starting database seed...")
        org   = seed_organization(db)
        users = seed_users(db, org)
        seed_documents(db, org, users)
        seed_calibration(db, org, users)
        seed_training(db, org, users)
        seed_capa(db, org, users)
        db.commit()
        logger.info("Seed complete.")
        print("\n" + "="*50)
        print("  Demo Credentials (passwords NO special chars)")
        print("="*50)
        print("  Admin:   admin@nexusfood.com.my     Admin1234")
        print("  Manager: quality.manager@nexusfood.com.my  Manager1234")
        print("  Viewer:  lab.microbio@nexusfood.com.my  Viewer1234")
        print("="*50 + "\n")
    except Exception as e:
        db.rollback()
        logger.error("Seed failed: %s", e)
        raise
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()

"""
Seed script — populates the database with realistic demo data for a
food-testing laboratory (Nexus Food Analytics Sdn Bhd).

Run via:  python -m app.utils.seed
Or auto-run on first startup if SEED_DEMO_DATA=true
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
    AuditLog,
)
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

TODAY = date.today()


def _d(offset: int) -> date:
    """Return a date relative to today."""
    return TODAY + timedelta(days=offset)


# ─── Organization ─────────────────────────────────────────────────────────────

def seed_organization(db: Session) -> Organization:
    existing = db.query(Organization).filter_by(slug="nexus-food-analytics").first()
    if existing:
        return existing

    org = Organization(
        id=uuid.uuid4(),
        name="Nexus Food Analytics Sdn Bhd",
        slug="nexus-food-analytics",
        industry="food_testing",
        address="No. 12, Jalan Teknologi 3, Taman Sains Selangor, 47810 Petaling Jaya, Selangor",
        contact_email="quality@nexusfood.com.my",
        is_active=True,
    )
    db.add(org)
    db.flush()
    logger.info("Seeded organization: %s", org.name)
    return org


# ─── Users ────────────────────────────────────────────────────────────────────

def seed_users(db: Session, org: Organization) -> dict[str, User]:
    users_data = [
        {
            "email": "admin@nexusfood.com.my",
            "full_name": "Dr. Amirah Zulkifli",
            "job_title": "Laboratory Director",
            "department": "Management",
            "role": UserRole.ADMIN,
            "password": "Admin@1234",
        },
        {
            "email": "quality.manager@nexusfood.com.my",
            "full_name": "Hafizuddin Ramli",
            "job_title": "Quality Manager",
            "department": "Quality Assurance",
            "role": UserRole.MANAGER,
            "password": "Manager@1234",
        },
        {
            "email": "compliance@nexusfood.com.my",
            "full_name": "Nurul Ain Ibrahim",
            "job_title": "Compliance Officer",
            "department": "Quality Assurance",
            "role": UserRole.MANAGER,
            "password": "Manager@1234",
        },
        {
            "email": "lab.microbio@nexusfood.com.my",
            "full_name": "Tan Wei Liang",
            "job_title": "Senior Microbiologist",
            "department": "Microbiology",
            "role": UserRole.VIEWER,
            "password": "Viewer@1234",
        },
        {
            "email": "lab.chem@nexusfood.com.my",
            "full_name": "Priya Krishnamoorthy",
            "job_title": "Analytical Chemist",
            "department": "Chemistry",
            "role": UserRole.VIEWER,
            "password": "Viewer@1234",
        },
        {
            "email": "lab.tech@nexusfood.com.my",
            "full_name": "Muhammad Faizal Othman",
            "job_title": "Lab Technician",
            "department": "Microbiology",
            "role": UserRole.VIEWER,
            "password": "Viewer@1234",
        },
    ]

    created: dict[str, User] = {}
    for data in users_data:
        existing = db.query(User).filter_by(email=data["email"]).first()
        if existing:
            created[data["email"]] = existing
            continue
        user = User(
            id=uuid.uuid4(),
            org_id=org.id,
            email=data["email"],
            hashed_password=hash_password(data["password"]),
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


# ─── Documents ────────────────────────────────────────────────────────────────

def seed_documents(db: Session, org: Organization, users: dict[str, User]) -> None:
    manager = users["quality.manager@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]
    chemist = users["lab.chem@nexusfood.com.my"]
    microbio = users["lab.microbio@nexusfood.com.my"]

    docs_data = [
        # ── Active SOPs ───────────────────────────────────
        {
            "title": "SOP for Microbial Enumeration by Pour Plate Method",
            "doc_number": "SOP-MB-001",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Microbiology",
            "version": 3,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(180),
            "effective_date": _d(-365),
            "owner": microbio,
        },
        {
            "title": "SOP for Total Coliform Detection by MPN Method",
            "doc_number": "SOP-MB-002",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Microbiology",
            "version": 2,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(90),
            "effective_date": _d(-270),
            "owner": microbio,
        },
        {
            "title": "SOP for Heavy Metal Analysis by ICP-MS",
            "doc_number": "SOP-CH-001",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Chemistry",
            "version": 4,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(210),
            "effective_date": _d(-150),
            "owner": chemist,
        },
        {
            "title": "SOP for Pesticide Residue Screening by GC-MS/MS",
            "doc_number": "SOP-CH-002",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Chemistry",
            "version": 2,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(45),
            "effective_date": _d(-320),
            "owner": chemist,
        },
        {
            "title": "SOP for Sample Receipt and Registration",
            "doc_number": "SOP-QA-001",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Quality Assurance",
            "version": 5,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(300),
            "effective_date": _d(-65),
            "owner": manager,
        },
        {
            "title": "SOP for Internal Audit Procedure",
            "doc_number": "SOP-QA-002",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_9001,
            "department": "Quality Assurance",
            "version": 2,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(240),
            "effective_date": _d(-125),
            "owner": compliance,
        },
        {
            "title": "SOP for Handling Non-Conforming Test Results",
            "doc_number": "SOP-QA-003",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Quality Assurance",
            "version": 3,
            "status": DocumentStatus.ACTIVE,
            "expiry_date": _d(160),
            "effective_date": _d(-205),
            "owner": manager,
        },
        # ── Expiring Soon ──────────────────────────────────
        {
            "title": "SOP for Autoclave Operation and Validation",
            "doc_number": "SOP-MB-005",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Microbiology",
            "version": 2,
            "status": DocumentStatus.EXPIRING_SOON,
            "expiry_date": _d(25),
            "effective_date": _d(-340),
            "owner": microbio,
        },
        {
            "title": "Quality Manual Rev 7",
            "doc_number": "QM-001",
            "doc_type": DocumentType.POLICY,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Quality Assurance",
            "version": 7,
            "status": DocumentStatus.EXPIRING_SOON,
            "expiry_date": _d(12),
            "effective_date": _d(-353),
            "owner": manager,
        },
        {
            "title": "SOP for Calibration of Analytical Balances",
            "doc_number": "SOP-EQ-003",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Chemistry",
            "version": 1,
            "status": DocumentStatus.EXPIRING_SOON,
            "expiry_date": _d(6),
            "effective_date": _d(-359),
            "owner": chemist,
        },
        # ── Expired ────────────────────────────────────────
        {
            "title": "SOP for Aflatoxin Detection by HPLC",
            "doc_number": "SOP-CH-008",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Chemistry",
            "version": 2,
            "status": DocumentStatus.EXPIRED,
            "expiry_date": _d(-15),
            "effective_date": _d(-380),
            "owner": chemist,
        },
        {
            "title": "Laboratory Safety Policy",
            "doc_number": "POL-HSE-001",
            "doc_type": DocumentType.POLICY,
            "compliance_category": ComplianceCategory.OSHA,
            "department": "Management",
            "version": 4,
            "status": DocumentStatus.EXPIRED,
            "expiry_date": _d(-32),
            "effective_date": _d(-397),
            "owner": compliance,
        },
        {
            "title": "Method Validation Protocol — Listeria spp.",
            "doc_number": "MVP-MB-002",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Microbiology",
            "version": 1,
            "status": DocumentStatus.EXPIRED,
            "expiry_date": _d(-8),
            "effective_date": _d(-373),
            "owner": microbio,
        },
        # ── Drafts ────────────────────────────────────────
        {
            "title": "SOP for Environmental Monitoring Programme",
            "doc_number": "SOP-MB-010",
            "doc_type": DocumentType.SOP,
            "compliance_category": ComplianceCategory.ISO_17025,
            "department": "Microbiology",
            "version": 1,
            "status": DocumentStatus.DRAFT,
            "expiry_date": None,
            "effective_date": None,
            "owner": microbio,
        },
        {
            "title": "Data Integrity Policy",
            "doc_number": "POL-QA-005",
            "doc_type": DocumentType.POLICY,
            "compliance_category": ComplianceCategory.GMP,
            "department": "Quality Assurance",
            "version": 1,
            "status": DocumentStatus.DRAFT,
            "expiry_date": None,
            "effective_date": None,
            "owner": compliance,
        },
    ]

    for data in docs_data:
        existing = db.query(Document).filter_by(
            org_id=org.id, doc_number=data["doc_number"]
        ).first()
        if existing:
            continue

        doc = Document(
            id=uuid.uuid4(),
            org_id=org.id,
            owner_id=data["owner"].id,
            title=data["title"],
            doc_number=data["doc_number"],
            doc_type=data["doc_type"],
            compliance_category=data["compliance_category"],
            department=data["department"],
            version=data["version"],
            is_latest=True,
            status=data["status"],
            expiry_date=data["expiry_date"],
            effective_date=data["effective_date"],
            file_type="pdf",
        )
        db.add(doc)

    db.flush()
    logger.info("Seeded %d documents", len(docs_data))


# ─── Calibration Records ──────────────────────────────────────────────────────

def seed_calibration(db: Session, org: Organization, users: dict[str, User]) -> None:
    chemist = users["lab.chem@nexusfood.com.my"]
    manager = users["quality.manager@nexusfood.com.my"]

    calibrations = [
        # Current
        ("Analytical Balance A&D GH-252", "EQ-BAL-001", "Chemistry",
         _d(-30), _d(335), CalibrationStatus.CURRENT, chemist),
        ("Analytical Balance Mettler Toledo MS204S", "EQ-BAL-002", "Chemistry",
         _d(-60), _d(305), CalibrationStatus.CURRENT, chemist),
        ("pH Meter Mettler Toledo S210", "EQ-PH-001", "Chemistry",
         _d(-15), _d(350), CalibrationStatus.CURRENT, chemist),
        ("Autoclave Tuttnauer 2540E", "EQ-AUT-001", "Microbiology",
         _d(-45), _d(320), CalibrationStatus.CURRENT, manager),
        ("Incubator Memmert IN55", "EQ-INC-001", "Microbiology",
         _d(-20), _d(345), CalibrationStatus.CURRENT, manager),
        ("HPLC Agilent 1260 Infinity II", "EQ-HPLC-001", "Chemistry",
         _d(-90), _d(275), CalibrationStatus.CURRENT, chemist),
        ("ICP-MS Agilent 7900", "EQ-ICP-001", "Chemistry",
         _d(-10), _d(355), CalibrationStatus.CURRENT, chemist),
        # Due Soon
        ("GC-MS/MS Shimadzu GCMS-TQ8050", "EQ-GCMS-001", "Chemistry",
         _d(-330), _d(22), CalibrationStatus.DUE_SOON, chemist),
        ("Pipette Calibration Set (Class A)", "EQ-PIP-001", "Quality Assurance",
         _d(-340), _d(18), CalibrationStatus.DUE_SOON, manager),
        ("Refrigerator Thermometer Logger", "EQ-LOG-001", "Microbiology",
         _d(-355), _d(10), CalibrationStatus.DUE_SOON, manager),
        # Overdue
        ("Spectrophotometer UV-Vis Shimadzu UV-1900", "EQ-SPEC-001", "Chemistry",
         _d(-400), _d(-35), CalibrationStatus.OVERDUE, chemist),
        ("Thermometer (Reference NIST)", "EQ-TEMP-001", "Quality Assurance",
         _d(-410), _d(-5), CalibrationStatus.OVERDUE, manager),
    ]

    for name, eq_id, dept, last_cal, next_due, status, assignee in calibrations:
        existing = db.query(CalibrationRecord).filter_by(
            org_id=org.id, equipment_id=eq_id
        ).first()
        if existing:
            continue

        rec = CalibrationRecord(
            id=uuid.uuid4(),
            org_id=org.id,
            assigned_to=assignee.id,
            equipment_name=name,
            equipment_id=eq_id,
            department=dept,
            last_calibrated=last_cal,
            next_due=next_due,
            calibration_interval_days=365,
            status=status,
            calibrated_by="Metrology Malaysia (SIRIM QAS)",
        )
        db.add(rec)

    db.flush()
    logger.info("Seeded calibration records")


# ─── Training Records ─────────────────────────────────────────────────────────

def seed_training(db: Session, org: Organization, users: dict[str, User]) -> None:
    microbio = users["lab.microbio@nexusfood.com.my"]
    chemist = users["lab.chem@nexusfood.com.my"]
    manager = users["quality.manager@nexusfood.com.my"]
    tech = users["lab.tech@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]

    trainings = [
        # Current
        (microbio, "ISO/IEC 17025:2017 Awareness Training",
         TrainingType.QUALITY_SYSTEMS, _d(-180), _d(185), TrainingStatus.CURRENT),
        (chemist, "ISO/IEC 17025:2017 Awareness Training",
         TrainingType.QUALITY_SYSTEMS, _d(-180), _d(185), TrainingStatus.CURRENT),
        (manager, "Internal Auditor Course — ISO 17025",
         TrainingType.QUALITY_SYSTEMS, _d(-90), _d(275), TrainingStatus.CURRENT),
        (compliance, "CAPA Management Best Practices",
         TrainingType.REGULATORY, _d(-60), _d(305), TrainingStatus.CURRENT),
        (microbio, "Biosafety Level 2 Laboratory Practices",
         TrainingType.SAFETY, _d(-200), _d(165), TrainingStatus.CURRENT),
        (tech, "Good Laboratory Practices (GLP) Foundation",
         TrainingType.QUALITY_SYSTEMS, _d(-30), _d(335), TrainingStatus.CURRENT),
        (chemist, "ICP-MS Operation — Agilent 7900",
         TrainingType.EQUIPMENT, _d(-15), _d(350), TrainingStatus.CURRENT),
        (microbio, "Microbial Identification using MALDI-TOF",
         TrainingType.EQUIPMENT, _d(-45), _d(320), TrainingStatus.CURRENT),
        # Due Soon
        (tech, "Chemical Safety and COSHH Awareness",
         TrainingType.SAFETY, _d(-340), _d(25), TrainingStatus.DUE_SOON),
        (microbio, "Proficiency Testing — PT Scheme Participation",
         TrainingType.REGULATORY, _d(-350), _d(15), TrainingStatus.DUE_SOON),
        (chemist, "Laboratory Safety Refresher",
         TrainingType.SAFETY, _d(-355), _d(10), TrainingStatus.DUE_SOON),
        # Overdue
        (tech, "ISO/IEC 17025:2017 Awareness Training",
         TrainingType.QUALITY_SYSTEMS, _d(-400), _d(-35), TrainingStatus.OVERDUE),
        (manager, "Emergency Response and First Aid",
         TrainingType.SAFETY, _d(-420), _d(-55), TrainingStatus.OVERDUE),
        # Completed (no expiry)
        (compliance, "MS ISO/IEC 17025 Lead Assessor",
         TrainingType.EXTERNAL_COURSE, _d(-500), None, TrainingStatus.COMPLETED),
        (manager, "Risk Management in Testing Laboratories",
         TrainingType.QUALITY_SYSTEMS, _d(-300), None, TrainingStatus.COMPLETED),
    ]

    for user, title, t_type, completed, expiry, status in trainings:
        existing = db.query(TrainingRecord).filter_by(
            org_id=org.id, user_id=user.id, training_title=title
        ).first()
        if existing:
            continue

        rec = TrainingRecord(
            id=uuid.uuid4(),
            org_id=org.id,
            user_id=user.id,
            training_title=title,
            training_type=t_type,
            completed_date=completed,
            expiry_date=expiry,
            status=status,
        )
        db.add(rec)

    db.flush()
    logger.info("Seeded training records")


# ─── CAPA Items ───────────────────────────────────────────────────────────────

def seed_capa(db: Session, org: Organization, users: dict[str, User]) -> None:
    manager = users["quality.manager@nexusfood.com.my"]
    compliance = users["compliance@nexusfood.com.my"]
    chemist = users["lab.chem@nexusfood.com.my"]
    microbio = users["lab.microbio@nexusfood.com.my"]

    capas = [
        {
            "reference_no": "CAPA-2024-001",
            "title": "Expired SOPs not flagged during monthly document review",
            "capa_type": CapaType.CORRECTIVE,
            "priority": CapaPriority.HIGH,
            "department": "Quality Assurance",
            "status": CapaStatus.CLOSED,
            "raised_date": _d(-120),
            "due_date": _d(-60),
            "closed_date": _d(-65),
            "raised_by": compliance,
            "assigned_to": manager,
            "source": "Internal Audit",
            "root_cause": "No automated reminder system for document expiry. Manual tracking spreadsheet missed 3 entries.",
            "action_taken": "Implemented document management system with automated email alerts.",
        },
        {
            "reference_no": "CAPA-2024-002",
            "title": "Calibration certificate for HPLC not renewed within 30-day grace period",
            "capa_type": CapaType.CORRECTIVE,
            "priority": CapaPriority.CRITICAL,
            "department": "Chemistry",
            "status": CapaStatus.CLOSED,
            "raised_date": _d(-90),
            "due_date": _d(-45),
            "closed_date": _d(-48),
            "raised_by": manager,
            "assigned_to": chemist,
            "source": "External Assessment",
            "root_cause": "Responsible person on leave; no backup designated for calibration tracking.",
            "action_taken": "Assigned primary and secondary owners for all critical equipment. Escalation email added.",
        },
        {
            "reference_no": "CAPA-2024-003",
            "title": "Technician performed testing without valid competency assessment record",
            "capa_type": CapaType.CORRECTIVE,
            "priority": CapaPriority.HIGH,
            "department": "Microbiology",
            "status": CapaStatus.IN_PROGRESS,
            "raised_date": _d(-45),
            "due_date": _d(15),
            "closed_date": None,
            "raised_by": manager,
            "assigned_to": microbio,
            "source": "Internal Audit",
            "root_cause": "Training matrix not updated after staff transfer between departments.",
        },
        {
            "reference_no": "CAPA-2024-004",
            "title": "Temperature excursion in sample storage refrigerator (Unit REF-03) on 3 occasions",
            "capa_type": CapaType.CORRECTIVE,
            "priority": CapaPriority.CRITICAL,
            "department": "Microbiology",
            "status": CapaStatus.IN_PROGRESS,
            "raised_date": _d(-30),
            "due_date": _d(30),
            "closed_date": None,
            "raised_by": compliance,
            "assigned_to": manager,
            "source": "Equipment Monitoring Log",
            "root_cause": "Door seal degraded; alarm threshold set too wide (±5°C vs required ±2°C).",
        },
        {
            "reference_no": "CAPA-2024-005",
            "title": "Preventive review of proficiency testing performance — below satisfactory score",
            "capa_type": CapaType.PREVENTIVE,
            "priority": CapaPriority.MEDIUM,
            "department": "Chemistry",
            "status": CapaStatus.OPEN,
            "raised_date": _d(-20),
            "due_date": _d(40),
            "closed_date": None,
            "raised_by": manager,
            "assigned_to": chemist,
            "source": "PT Scheme Report",
        },
        {
            "reference_no": "CAPA-2024-006",
            "title": "SOP for pesticide residue screening (SOP-CH-002) requires update — new LC-MS/MS method",
            "capa_type": CapaType.IMPROVEMENT,
            "priority": CapaPriority.MEDIUM,
            "department": "Chemistry",
            "status": CapaStatus.OPEN,
            "raised_date": _d(-10),
            "due_date": _d(50),
            "closed_date": None,
            "raised_by": chemist,
            "assigned_to": manager,
            "source": "Method Review Meeting",
        },
        {
            "reference_no": "CAPA-2024-007",
            "title": "Laboratory Safety Policy (POL-HSE-001) overdue for renewal — 32 days past expiry",
            "capa_type": CapaType.CORRECTIVE,
            "priority": CapaPriority.HIGH,
            "department": "Management",
            "status": CapaStatus.OVERDUE,
            "raised_date": _d(-20),
            "due_date": _d(-5),
            "closed_date": None,
            "raised_by": compliance,
            "assigned_to": manager,
            "source": "Document Expiry Review",
        },
    ]

    for data in capas:
        existing = db.query(CapaItem).filter_by(
            org_id=org.id, reference_no=data["reference_no"]
        ).first()
        if existing:
            continue

        item = CapaItem(
            id=uuid.uuid4(),
            org_id=org.id,
            reference_no=data["reference_no"],
            title=data["title"],
            capa_type=data["capa_type"],
            priority=data["priority"],
            department=data["department"],
            status=data["status"],
            raised_date=data["raised_date"],
            due_date=data["due_date"],
            closed_date=data.get("closed_date"),
            raised_by=data["raised_by"].id,
            assigned_to=data["assigned_to"].id,
            source=data.get("source"),
            root_cause=data.get("root_cause"),
            action_taken=data.get("action_taken"),
        )
        db.add(item)

    db.flush()
    logger.info("Seeded CAPA items")


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_seed(db: Session | None = None) -> None:
    """Run all seed functions. Pass an existing session or let it create one."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        logger.info("Starting database seed...")
        org = seed_organization(db)
        users = seed_users(db, org)
        seed_documents(db, org, users)
        seed_calibration(db, org, users)
        seed_training(db, org, users)
        seed_capa(db, org, users)
        db.commit()
        logger.info("Seed complete.")
        _print_credentials()
    except Exception as e:
        db.rollback()
        logger.error("Seed failed: %s", e)
        raise
    finally:
        if close_session:
            db.close()


def _print_credentials() -> None:
    print("\n" + "="*55)
    print("  LabAudit Demo Credentials")
    print("="*55)
    print("  Role     Email                              Password")
    print("-"*55)
    print("  Admin    admin@nexusfood.com.my             Admin@1234")
    print("  Manager  quality.manager@nexusfood.com.my  Manager@1234")
    print("  Manager  compliance@nexusfood.com.my       Manager@1234")
    print("  Viewer   lab.microbio@nexusfood.com.my     Viewer@1234")
    print("  Viewer   lab.chem@nexusfood.com.my         Viewer@1234")
    print("  Viewer   lab.tech@nexusfood.com.my         Viewer@1234")
    print("="*55 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()

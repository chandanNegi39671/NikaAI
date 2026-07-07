"""
backend/app/core/db_init.py
───────────────────────────
Database schema creation and seeding.
"""

from __future__ import annotations

from app.core.database import Base, engine, SessionLocal
from app.models.db_models import User, Machine, Worker, Shift, FactoryMemory, Session as DbSession
from app.core.logging import get_logger

logger = get_logger(__name__)

def init_db() -> None:
    """Initialize database tables and seed them with default operational metadata if empty."""
    logger.info("Initializing database and checking schemas...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified.")
    except Exception as exc:
        logger.error(f"Failed to create database tables: {exc}")
        raise exc

    db = SessionLocal()
    try:
        # 1. Seed Workers
        if db.query(Worker).count() == 0:
            logger.info("Seeding default workers...")
            w1 = Worker(name="Ravi Singh", employee_code="EMP001", role="operator")
            w2 = Worker(name="Priya Sharma", employee_code="EMP002", role="manager")
            w3 = Worker(name="Vikram Patel", employee_code="EMP003", role="admin")
            db.add_all([w1, w2, w3])
            db.commit()

            # Seed Shifts using seeded worker ids
            logger.info("Seeding default shifts...")
            s1 = Shift(name="Day", start_time="06:00:00", end_time="14:00:00", worker_id=w1.id)
            s2 = Shift(name="Evening", start_time="14:00:00", end_time="22:00:00", worker_id=w2.id)
            s3 = Shift(name="Night", start_time="22:00:00", end_time="06:00:00", worker_id=w3.id)
            db.add_all([s1, s2, s3])
            db.commit()
        
        # 2. Seed Machines
        if db.query(Machine).count() == 0:
            logger.info("Seeding default machines...")
            m1 = Machine(name="CNC Press 01", model_number="CNC-XP1", status="operational", location="Zone A")
            m2 = Machine(name="Welding Station A", model_number="WLD-M2", status="operational", location="Zone B")
            m3 = Machine(name="Assembly Line 3", model_number="ASM-L3", status="operational", location="Zone C")
            db.add_all([m1, m2, m3])
            db.commit()

        # 3. Seed Users
        if db.query(User).count() == 0:
            logger.info("Seeding default users...")
            u1 = User(username="operator1", email="operator1@nika.ai", password_hash="pbkdf2:sha256:...", role="operator")
            u2 = User(username="manager1", email="manager1@nika.ai", password_hash="pbkdf2:sha256:...", role="manager")
            u3 = User(username="admin1", email="admin1@nika.ai", password_hash="pbkdf2:sha256:...", role="admin")
            db.add_all([u1, u2, u3])
            db.commit()

        # 4. Seed Factory Memory Defect Guidelines
        if db.query(FactoryMemory).count() == 0:
            logger.info("Seeding default Factory Memory guidelines...")
            fm1 = FactoryMemory(
                defect_class="surface_crack",
                description="Linear fracture patterns visible on metal surfaces.",
                recurring_defect_pattern="Often correlates with high heat cycles during late shifts (Evening/Night) on CNC Press 01.",
                recommended_action="1. Stop machine immediately.\n2. Verify coolant fluid pressure.\n3. Request dye penetrant inspection."
            )
            fm2 = FactoryMemory(
                defect_class="scratch",
                description="Linear abrasive markings indicating mechanical friction.",
                recurring_defect_pattern="Commonly occurs during manual material handling or faulty guides in Assembly Line 3.",
                recommended_action="1. Check conveyance belt guides.\n2. Re-align robotic pickup head.\n3. Clean surface protective covers."
            )
            fm3 = FactoryMemory(
                defect_class="dent",
                description="Localized depression caused by force/impact.",
                recurring_defect_pattern="Frequently associated with incorrect hydraulic press pressure settings.",
                recommended_action="1. Inspect stamping mold alignment.\n2. Calibrate hydraulic pressure threshold.\n3. Inspect ejector pins."
            )
            db.add_all([fm1, fm2, fm3])
            db.commit()

        logger.info("Database seeding complete.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Error during database seeding: {exc}")
        raise exc
    finally:
        db.close()

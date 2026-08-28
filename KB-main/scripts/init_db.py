"""
Initialize the database: create all tables and seed demo users + roles.
Run: python scripts/init_db.py
"""
import sys
from pathlib import Path

# Add project root to path so we can import backend modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import engine, SessionLocal, Base
from backend.models import User, Role, user_roles


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created.")


def seed_roles(db):
    """Seed the 5 roles."""
    role_names = ["Employee", "HR", "Engineer", "Sales", "Admin"]
    created = 0
    for name in role_names:
        existing = db.query(Role).filter(Role.role_name == name).first()
        if not existing:
            db.add(Role(role_name=name))
            created += 1
    db.commit()
    print(f"✓ {created} roles seeded ({len(role_names) - created} already existed).")


def seed_users(db):
    """Seed 5 demo users with their roles."""
    demo_users = [
        {"user_id": "amrutha",  "email": "amrutha@company.com",  "department": "HR",          "roles": ["Employee", "HR"]},
        {"user_id": "harshini", "email": "harshini@company.com", "department": "Engineering", "roles": ["Employee", "Engineer"]},
        {"user_id": "tanvi",    "email": "tanvi@company.com",    "department": "Sales",       "roles": ["Employee", "Sales"]},
        {"user_id": "bhaskar",  "email": "bhaskar@company.com",  "department": "Engineering", "roles": ["Employee", "Admin"]},
        {"user_id": "arijith",  "email": "arijith@company.com",  "department": "HR",          "roles": ["Employee"]},
    ]
    created = 0
    for u in demo_users:
        existing = db.query(User).filter(User.user_id == u["user_id"]).first()
        if not existing:
            user = User(user_id=u["user_id"], email=u["email"], department=u["department"])
            # Attach roles
            for role_name in u["roles"]:
                role = db.query(Role).filter(Role.role_name == role_name).first()
                if role:
                    user.roles.append(role)
            db.add(user)
            created += 1
    db.commit()
    print(f"✓ {created} users seeded ({len(demo_users) - created} already existed).")


def main():
    print("=== Knowledge Base — Database Initialization ===\n")
    init_db()

    db = SessionLocal()
    try:
        seed_roles(db)
        seed_users(db)
    finally:
        db.close()

    print("\n=== Done! Database is ready. ===")


if __name__ == "__main__":
    main()

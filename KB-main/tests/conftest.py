"""Pytest fixtures."""
import os
import sys
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Check Postgres connectivity before importing backend modules
test_db_file = ROOT / "test_kb_sqlite.db"
def _is_pg_up():
    try:
        s = socket.create_connection(("localhost", 5432), timeout=0.5)
        s.close()
        return True
    except OSError:
        return False

if not _is_pg_up():
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file.as_posix()}"

from backend.main import app
from backend.services.auth import create_token


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database is accessible; if PostgreSQL is offline, use SQLite fallback."""
    from backend.database import engine, SessionLocal, Base
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        import backend.database as db_mod
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        test_db_path = ROOT / "test_kb_sqlite.db"
        sqlite_engine = create_engine(
            f"sqlite:///{test_db_path.as_posix()}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
        db_mod.engine = sqlite_engine
        db_mod.SessionLocal = sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(bind=sqlite_engine)
        from scripts.init_db import seed_roles, seed_users
        db = db_mod.SessionLocal()
        try:
            seed_roles(db)
            seed_users(db)
        finally:
            db.close()
        yield
        try:
            if test_db_path.exists():
                test_db_path.unlink()
        except Exception:
            pass
        return
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    return create_token("bhaskar")


@pytest.fixture
def engineer_token():
    return create_token("harshini")


@pytest.fixture
def hr_token():
    return create_token("amrutha")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def engineer_headers(engineer_token):
    return {"Authorization": f"Bearer {engineer_token}"}


@pytest.fixture
def hr_headers(hr_token):
    return {"Authorization": f"Bearer {hr_token}"}


@pytest.fixture
def sample_md(tmp_path):
    p = tmp_path / "sample.md"
    p.write_text("# Title\n\nHello world policy text.\n", encoding="utf-8")
    return p


@pytest.fixture
def sample_pdf(tmp_path):
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf2 not installed")
    p = tmp_path / "sample.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, "Page one content about PTO policy.")
    pdf.add_page()
    pdf.multi_cell(0, 8, "Page two content about remote work.")
    pdf.output(str(p))
    return p

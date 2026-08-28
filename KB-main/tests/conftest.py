"""Pytest fixtures."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.main import app
from backend.services.auth import create_token


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

def test_upload_forbidden_non_admin(client, engineer_headers, tmp_path):
    f = tmp_path / "note.md"
    f.write_text("# Note\n\nTest upload.", encoding="utf-8")
    with open(f, "rb") as fh:
        r = client.post(
            "/api/documents/upload",
            headers=engineer_headers,
            files={"file": ("note.md", fh, "text/markdown")},
            data={
                "title": "Engineer Upload Test",
                "department": "Engineering",
                "classification": "public",
            },
        )
    assert r.status_code == 403


def test_upload_admin(client, admin_headers, tmp_path):
    f = tmp_path / "admin_note.md"
    f.write_text("# Admin Note\n\nUploaded by pytest.", encoding="utf-8")
    with open(f, "rb") as fh:
        r = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            files={"file": ("admin_note.md", fh, "text/markdown")},
            data={
                "title": "Pytest Admin Upload",
                "department": "Engineering",
                "classification": "public",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["chunks_indexed"] >= 1
    assert data["doc_id"]

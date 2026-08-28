#!/usr/bin/env python3
"""API smoke tests. Default: localhost:8000. Set SMOKE_API_BASE for production."""
import json
import sys
import urllib.error
import urllib.request

import os

_BASE_ROOT = os.environ.get("SMOKE_API_BASE", "http://localhost:8000").rstrip("/")
BASE = f"{_BASE_ROOT}/api"


def req(method, path, body=None, token=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        try:
            detail = json.loads(body_text)
        except json.JSONDecodeError:
            detail = body_text
        return e.code, detail


def login(email):
    code, data = req("POST", "/auth/login", {"email": email})
    assert code == 200, f"login {email}: {code} {data}"
    return data["token"]


def main():
    results = []
    failed = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        if not ok:
            failed.append(name)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail and not ok else ""))

    print("=== API smoke tests ===\n")

    code, health = req("GET", "/health")
    check("Health", code == 200 and health.get("status") == "ok")
    check("Postgres up", health.get("components", {}).get("postgres") == "up")
    check("Qdrant up", health.get("components", {}).get("qdrant") == "up")

    code, _ = req("POST", "/auth/login", {"email": "nobody@company.com"})
    check("Login rejects unknown user", code == 401 or code == 404)

    admin = login("bhaskar@company.com")
    hr = login("amrutha@company.com")
    engineer = login("harshini@company.com")
    sales = login("tanvi@company.com")
    check("Demo user logins", True)

    code, docs = req("GET", "/documents", token=admin)
    check("List documents", code == 200 and docs.get("total", 0) >= 30)
    doc_list = docs.get("documents", [])
    pdf_docs = [d for d in doc_list if d.get("file_type") == "pdf"]
    check("PDF documents in library", len(pdf_docs) >= 5, f"found {len(pdf_docs)}")

    code, search = req(
        "POST",
        "/search",
        {"query": "What is the PTO policy?", "department_filter": "HR"},
        token=admin,
    )
    cites = search.get("citations", []) if code == 200 else []
    check("Search returns answer", code == 200 and bool(search.get("answer")))
    check(
        "Search returns citations",
        len(cites) >= 1 or search.get("chunks_found", 0) >= 1,
        f"citations={len(cites)} chunks={search.get('chunks_found')}",
    )
    check(
        "Citation has chunk_text",
        len(cites) >= 1 and all(c.get("chunk_text") for c in cites),
        f"count={len(cites)}",
    )

    if cites:
        doc_id = cites[0]["doc_id"]
        excerpt = cites[0]["chunk_text"][:200]
        from urllib.parse import quote

        qs = f"?highlight={quote(excerpt)}"
        code, doc = req("GET", f"/documents/{doc_id}{qs}", token=admin)
        check("Get document with highlight", code == 200 and bool(doc.get("content")))

    code, eng_search = req(
        "POST",
        "/search",
        {"query": "salary bands compensation"},
        token=engineer,
    )
    if code != 200 or not isinstance(eng_search, dict):
        check("Engineer RBAC hides compensation", False, f"search HTTP {code}: {eng_search}")
        eng_titles = ""
    else:
        eng_titles = " ".join(
            c.get("doc_title", "") for c in eng_search.get("citations", [])
        ).lower()
    if code == 200 and isinstance(eng_search, dict):
        check(
            "Engineer RBAC hides compensation",
            "compensation" not in eng_titles,
        )

    code, admin_search = req(
        "POST",
        "/search",
        {"query": "salary bands compensation"},
        token=admin,
    )
    admin_answer = (admin_search.get("answer") or "").lower()
    check(
        "Admin can access compensation topics",
        code == 200 and ("compensation" in admin_answer or "salary" in admin_answer),
    )

    # Multipart upload requires urllib differently — use stdlib boundary upload
    import io
    boundary = "----SmokeBoundary7MA4YWxk"
    body_io = io.BytesIO()
    for part in (
        f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\nTest\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="department"\r\n\r\nEngineering\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="classification"\r\n\r\npublic\r\n',
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="t.md"\r\nContent-Type: text/markdown\r\n\r\n# T\n\r\n'
        ),
        f"--{boundary}--\r\n",
    ):
        body_io.write(part.encode())
    upload_req = urllib.request.Request(
        f"{BASE}/documents/upload",
        data=body_io.getvalue(),
        headers={
            "Authorization": f"Bearer {engineer}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(upload_req, timeout=30) as resp:
            upload_code = resp.status
    except urllib.error.HTTPError as e:
        upload_code = e.code
    check("Upload forbidden for non-admin", upload_code == 403)

    code, sales_search = req(
        "POST",
        "/search",
        {"query": "pricing tiers"},
        token=sales,
    )
    check("Sales user search works", code == 200 and bool(sales_search.get("answer")))

    print(f"\n=== Summary: {len(results) - len(failed)}/{len(results)} passed ===")
    if failed:
        print("Failed:", ", ".join(failed))
        sys.exit(1)
    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

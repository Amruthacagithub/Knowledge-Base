/**
 * API client for Knowledge Base backend.
 * Local: omit VITE_API_URL (defaults to http://localhost:8000).
 * Production (Vercel): set VITE_API_URL to your Cloud Run URL (no trailing slash).
 */
const API_ROOT = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const BASE = `${API_ROOT}/api`;

function authHeaders(token) {
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };
}

export async function login(email) {
    const res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        const message =
            typeof detail === "string"
                ? detail
                : Array.isArray(detail)
                  ? detail.map((d) => d.msg || d).join("; ")
                  : "Login failed";
        throw new Error(message || "Login failed");
    }
    return res.json();
}

export async function search(token, query, departmentFilter = null) {
    const body = { query };
    if (departmentFilter) body.department_filter = departmentFilter;

    const res = await fetch(`${BASE}/search`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Search failed");
    }
    return res.json();
}

export async function fetchDocuments(token) {
    const res = await fetch(`${BASE}/documents`, {
        headers: authHeaders(token),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to load documents");
    }
    return res.json();
}

export async function fetchDocument(token, docId, highlights = null, page = null) {
    const params = new URLSearchParams();
    const list = highlights == null
        ? []
        : Array.isArray(highlights)
            ? highlights
            : [highlights];
    for (const h of list) {
        const excerpt = String(h).trim().slice(0, 1500);
        if (excerpt) params.append("highlight", excerpt);
    }
    if (page != null) params.set("page", String(page));
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${BASE}/documents/${encodeURIComponent(docId)}${qs}`, {
        headers: authHeaders(token),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to load document");
    }
    return res.json();
}

export function documentFileUrl(docId) {
    return `${BASE}/documents/${encodeURIComponent(docId)}/file`;
}

export async function openDocumentPdf(token, docId, page = 1) {
    const res = await fetch(documentFileUrl(docId), {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to open PDF");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(`${url}#page=${page}`, "_blank", "noopener,noreferrer");
}

export async function uploadDocument(token, formData) {
    const res = await fetch(`${BASE}/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Upload failed");
    }
    return res.json();
}

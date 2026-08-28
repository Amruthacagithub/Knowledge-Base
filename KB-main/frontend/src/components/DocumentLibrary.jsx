import { useEffect, useState } from "react";
import { fetchDocuments } from "../api";

export default function DocumentLibrary({ token, departmentFilter, onOpenDocument }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchDocuments(token)
      .then((data) => {
        if (!cancelled) {
          setDocs(data.documents || []);
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const filtered = docs.filter((d) => {
    if (departmentFilter && d.department !== departmentFilter) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      d.title.toLowerCase().includes(q) ||
      d.department.toLowerCase().includes(q)
    );
  });

  const byDept = filtered.reduce((acc, d) => {
    if (!acc[d.department]) acc[d.department] = [];
    acc[d.department].push(d);
    return acc;
  }, {});

  return (
    <section className="doc-library">
      <button
        type="button"
        className="doc-library-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <span>
          Your documents
          {!loading && <span className="doc-count"> ({docs.length})</span>}
        </span>
        <span className="chevron-icon">{expanded ? "▾" : "▸"}</span>
      </button>

      {expanded && (
        <div className="doc-library-body">
          <input
            type="search"
            className="doc-library-search"
            placeholder="Filter documents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {loading && <p className="doc-library-hint">Loading…</p>}
          {error && <p className="doc-library-error">{error}</p>}
          {!loading && !error && filtered.length === 0 && (
            <p className="doc-library-hint">No documents match.</p>
          )}
          {Object.entries(byDept).map(([dept, items]) => (
            <div key={dept} className="doc-dept-group">
              <span className="doc-dept-label">{dept}</span>
              <ul className="doc-list">
                {items.map((d) => (
                  <li key={d.id}>
                    <button
                      type="button"
                      className="doc-list-item"
                      onClick={() => onOpenDocument(d)}
                      title={d.title}
                    >
                      <span className="doc-list-title">{d.title}</span>
                      {d.file_type === "pdf" && (
                        <span className="doc-pdf-badge">PDF</span>
                      )}
                      {d.classification === "restricted" && (
                        <span className="doc-restricted-badge">restricted</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

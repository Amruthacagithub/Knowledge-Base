import { useEffect, useRef } from "react";
import MarkdownContent from "./MarkdownContent";
import { splitByExcerpts } from "../utils/highlightContent";
import { openDocumentPdf } from "../api";

function PageBadge({ page }) {
  if (!page) return null;
  return <span className="page-badge">Page {page}</span>;
}

export default function DocumentViewerModal({
  document,
  loading,
  error,
  authToken,
  onClose,
}) {
  const firstHighlightRef = useRef(null);
  const pageHighlightRef = useRef(null);

  const excerpts =
    document?.highlight_excerpts?.length > 0
      ? document.highlight_excerpts
      : document?.highlight_excerpt
        ? [document.highlight_excerpt]
        : [];

  const isPdf = document?.file_type === "pdf";
  const targetPage = document?.highlight_page || null;

  useEffect(() => {
    const el = pageHighlightRef.current || firstHighlightRef.current;
    if (document && el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [document]);

  if (!document && !loading && !error) return null;

  const handleOpenPdf = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (document && authToken) {
      openDocumentPdf(authToken, document.id, targetPage || 1);
    }
  };

  return (
    <div className="doc-modal-overlay" onClick={onClose} role="presentation">
      <div
        className="doc-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="doc-modal-title"
      >
        <header className="doc-modal-header">
          <div className="doc-modal-header-main">
            <h2 id="doc-modal-title">{document?.title || "Document"}</h2>
            {document && (
              <div className="doc-modal-meta">
                <span className={`panel-dept dept-${document.department?.toLowerCase()}`}>
                  {document.department}
                </span>
                <span className="doc-classification">{document.classification}</span>
                {isPdf && <span className="file-type-badge">PDF</span>}
                {targetPage && <PageBadge page={targetPage} />}
                {excerpts.length > 1 && (
                  <span className="doc-highlight-count">
                    {excerpts.length} referenced sections
                  </span>
                )}
              </div>
            )}
            {isPdf && authToken && (
              <button type="button" className="open-pdf-link" onClick={handleOpenPdf}>
                Open PDF
                <span className="view-source-arrow" aria-hidden="true">
                  ↗
                </span>
              </button>
            )}
          </div>
          <button type="button" className="panel-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className="doc-modal-body">
          {loading && <p className="doc-modal-loading">Loading document…</p>}
          {error && <p className="error-msg">{error}</p>}
          {document && isPdf && document.pages?.length > 0 && (
            <article className="doc-modal-content doc-modal-pdf">
              {document.pages.map((pg) => {
                const pageSegments = splitByExcerpts(pg.text, excerpts);
                const isTargetPage = targetPage === pg.page;
                return (
                  <section
                    key={pg.page}
                    id={`pdf-page-${pg.page}`}
                    ref={isTargetPage ? pageHighlightRef : undefined}
                    className="pdf-page-section"
                  >
                    <h3 className="pdf-page-heading">Page {pg.page}</h3>
                    {pageSegments.map((seg, i) => {
                      if (seg.type === "highlight") {
                        return (
                          <div key={i} className="doc-highlight-block">
                            <span className="doc-highlight-label">Referenced section</span>
                            <MarkdownContent
                              content={seg.text}
                              variant="source"
                              className="markdown-body markdown-doc"
                            />
                          </div>
                        );
                      }
                      if (!seg.text?.trim()) return null;
                      return (
                        <MarkdownContent
                          key={i}
                          content={seg.text}
                          variant="source"
                          className="markdown-body markdown-doc"
                        />
                      );
                    })}
                  </section>
                );
              })}
            </article>
          )}
          {document && !isPdf && (
            <article className="doc-modal-content">
              {splitByExcerpts(document.content, excerpts).map((seg, i) => {
                if (seg.type === "highlight") {
                  const isFirst = !splitByExcerpts(document.content, excerpts)
                    .slice(0, i)
                    .some((s) => s.type === "highlight");
                  return (
                    <section
                      key={`hl-${i}`}
                      ref={isFirst ? firstHighlightRef : undefined}
                      className="doc-highlight-block"
                    >
                      <span className="doc-highlight-label">Referenced section</span>
                      <MarkdownContent
                        content={seg.text}
                        variant="source"
                        className="markdown-body markdown-doc"
                      />
                    </section>
                  );
                }
                if (!seg.text?.trim()) return null;
                return (
                  <MarkdownContent
                    key={`norm-${i}`}
                    content={seg.text}
                    variant="source"
                    className="markdown-body markdown-doc"
                  />
                );
              })}
            </article>
          )}
        </div>
      </div>
    </div>
  );
}

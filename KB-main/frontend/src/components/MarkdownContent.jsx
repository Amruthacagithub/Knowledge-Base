import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Split text into parts, turning [1], [2] citation markers into clickable pills.
 */
function renderWithCitations(text, onCitationClick, selectedMarker) {
  if (!text || !onCitationClick) return text;
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1], 10);
      return (
        <button
          key={`cite-${i}-${num}`}
          type="button"
          className={`citation-pill ${selectedMarker === num ? "active" : ""}`}
          onClick={(e) => {
            e.preventDefault();
            onCitationClick(num);
          }}
        >
          {num}
        </button>
      );
    }
    return part;
  });
}

function TextWithCitations({ children, onCitationClick, selectedMarker }) {
  if (typeof children !== "string") {
    if (Array.isArray(children)) {
      return children.map((child, i) =>
        typeof child === "string" ? (
          <span key={i}>
            {renderWithCitations(child, onCitationClick, selectedMarker)}
          </span>
        ) : (
          child
        )
      );
    }
    return children;
  }
  return <>{renderWithCitations(children, onCitationClick, selectedMarker)}</>;
}

export default function MarkdownContent({
  content,
  className = "markdown-body",
  variant = "answer",
  citations = [],
  onCitationClick,
  selectedMarker = null,
}) {
  const handleCitationClick = (marker) => {
    if (!onCitationClick || !citations?.length) return;
    const c = citations.find((x) => x.marker === marker);
    if (c) onCitationClick(c);
  };

  const wrapText = (Tag) =>
    function Wrapped({ children, ...props }) {
      return (
        <Tag {...props}>
          <TextWithCitations
            onCitationClick={handleCitationClick}
            selectedMarker={selectedMarker}
          >
            {children}
          </TextWithCitations>
        </Tag>
      );
    };

  const components = {
    p: wrapText("p"),
    li: wrapText("li"),
    td: wrapText("td"),
    th: wrapText("th"),
    strong: ({ children }) => <strong>{children}</strong>,
    em: ({ children }) => <em>{children}</em>,
    h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
    h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
    h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
    ul: ({ children }) => <ul className="md-ul">{children}</ul>,
    ol: ({ children }) => <ol className="md-ol">{children}</ol>,
    table: ({ children }) => (
      <div className="md-table-wrap">
        <table className="md-table">{children}</table>
      </div>
    ),
    code: ({ className: cn, children, ...props }) => {
      const inline = !cn;
      if (inline) {
        return (
          <code className="md-code-inline" {...props}>
            {children}
          </code>
        );
      }
      return (
        <pre className="md-pre">
          <code className={cn} {...props}>
            {children}
          </code>
        </pre>
      );
    },
  };

  if (!content?.trim()) {
    return <p className={className}>No content available.</p>;
  }

  return (
    <div className={`${className} markdown-${variant}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

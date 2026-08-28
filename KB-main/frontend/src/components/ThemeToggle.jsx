import { applyTheme, resolveTheme } from "../theme";

export default function ThemeToggle({ theme, onThemeChange }) {
  const resolved = resolveTheme(theme);

  const toggle = () => {
    const next = resolved === "dark" ? "light" : "dark";
    applyTheme(next);
    onThemeChange(next);
  };

  const label = theme === "system" ? `Theme (${resolved})` : resolved === "dark" ? "Light mode" : "Dark mode";

  return (
    <button
      type="button"
      className="header-btn theme-toggle-btn"
      onClick={toggle}
      title={label}
      aria-label={label}
    >
      {resolved === "dark" ? "☀ Light" : "☾ Dark"}
    </button>
  );
}

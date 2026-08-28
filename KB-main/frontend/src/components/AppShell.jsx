export default function AppShell({ sidebar, main, panel, header, panelOpen }) {
  return (
    <div className={`app-shell ${panelOpen ? "sources-open" : "sources-closed"}`}>
      {header}
      <div className="shell-body">
        {sidebar}
        <main className="shell-main">{main}</main>
        {panelOpen && panel}
      </div>
    </div>
  );
}

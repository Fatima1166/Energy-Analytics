export default function DashboardPage() {
  // Point at 127.0.0.1 explicitly. Streamlit binds IPv4 only, but on this
  // machine `localhost` resolves to ::1 first (Node/Vite report
  // dns.getDefaultResultOrder() === "verbatim"), so a `localhost` iframe can
  // hit a refused IPv6 connection and render blank.
  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#0E1117' }}>
      <iframe
        src="http://127.0.0.1:8501"
        title="Pakistan Renewable Energy Outlook Dashboard"
        style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
      />
    </div>
  )
}


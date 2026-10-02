import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Check,
  CircleHelp,
  Clock3,
  Database,
  FolderClock,
  Globe2,
  Layers,
  LoaderCircle,
  Network,
  Play,
  Radio,
  RefreshCw,
  Save,
  ShieldCheck,
  Square,
  Trash2,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { request } from "./lib/api";
import { useLiveCapture } from "./hooks/useLiveCapture";
import { aggregate, bytes } from "./lib/analysis";
import type { Adapter, Session, Snapshot } from "./types";
import Chart from "./components/TrafficChart";
import Investigation from "./components/Investigation";
import LandingPage from "./components/LandingPage";

type Page = "overview" | "investigate" | "sessions" | "model";
const pageNames: Record<Page, string> = {
  overview: "Network overview",
  investigate: "Traffic explorer",
  sessions: "Saved sessions",
  model: "Model analysis",
};
const empty: Snapshot = {
  state: "idle",
  error: null,
  interface: null,
  packets: [],
  packet_count: 0,
  byte_count: 0,
  elapsed: 0,
  protocols: {},
  packet_rate: null,
  byte_rate: null,
  last_packet_age: null,
  history: [],
};
const nav: { id: Page; icon: LucideIcon; label: string }[] = [
  { id: "overview", icon: Activity, label: "Overview" },
  { id: "investigate", icon: Network, label: "Traffic explorer" },
  { id: "sessions", icon: FolderClock, label: "Saved sessions" },
  { id: "model", icon: BrainCircuit, label: "Model analysis" },
];
const utc = (value: string) =>
  new Date(value).toLocaleString(undefined, { timeZone: "UTC" }) + " UTC";

export default function App() {
  const { snapshot: live, connected } = useLiveCapture();
  const [view, setView] = useState<"landing" | "dashboard">(() => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.toLowerCase();
      if (hash === "#console" || hash === "#dashboard" || hash === "#monitoring") {
        return "dashboard";
      }
    }
    return "landing";
  });
  const [page, setPage] = useState<Page>("overview");
  const [adapters, setAdapters] = useState<Adapter[]>([]);
  const [adapter, setAdapter] = useState("");
  const [adapterError, setAdapterError] = useState("");
  const [adaptersLoading, setAdaptersLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [libraryError, setLibraryError] = useState("");
  const [saved, setSaved] = useState<{ id: string; snapshot: Snapshot } | null>(
    null,
  );
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dialog, setDialog] = useState<"save" | Session | null>(null);
  const [name, setName] = useState("");
  const [model, setModel] = useState({
    available: false,
    detail: "Checking model artifacts…",
  });
  const [prediction, setPrediction] = useState<{
    label: string;
    probabilities: Record<string, number>;
    packet_count: number;
    scope: string;
  } | null>(null);
  const snapshot = saved?.snapshot ?? live ?? empty;
  const active =
    !!live && ["starting", "running", "stopping"].includes(live.state);
  const scope = saved?.id ?? live?.capture_id ?? "live";
  const summary = useMemo(
    () => aggregate(snapshot.packets),
    [snapshot.packets],
  );
  const stale = !saved && !connected;
  const loadAdapters = async () => {
    setAdaptersLoading(true);
    try {
      const result = await request<{ interfaces: Adapter[]; default: string }>(
        "/interfaces",
      );
      setAdapters(result.interfaces);
      setAdapter((old) =>
        result.interfaces.some((a) => a.id === old) ? old : result.default,
      );
      setAdapterError("");
    } catch (e) {
      setAdapterError((e as Error).message);
    } finally {
      setAdaptersLoading(false);
    }
  };
  const loadSessions = async () => {
    try {
      setSessions(await request<Session[]>("/sessions"));
      setLibraryError("");
    } catch (e) {
      setLibraryError((e as Error).message);
    }
  };
  useEffect(() => {
    void loadAdapters();
    void loadSessions();
    request<typeof model>("/model")
      .then(setModel)
      .catch(() =>
        setModel({
          available: false,
          detail: "Model status unavailable. Check the backend connection.",
        }),
      );
  }, [connected]);
  useEffect(() => {
    setPrediction(null);
  }, [scope]);
  useEffect(() => {
    if (!dialog) return;
    const previous = document.activeElement as HTMLElement | null;
    const handle = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDialog(null);
    };
    document.addEventListener("keydown", handle);
    return () => {
      document.removeEventListener("keydown", handle);
      previous?.focus();
    };
  }, [dialog]);
  async function action(label: string, operation: () => Promise<void>) {
    setBusy(label);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  function openSave() {
    setName(`Capture ${new Date().toLocaleString()}`);
    setDialog("save");
  }
  const openSession = (session: Session) =>
    action("open", async () => {
      const data = await request<Snapshot>(`/sessions/${session.id}`);
      setSaved({ id: session.id, snapshot: data });
      setPage("overview");
    });
  const status = saved
    ? "Saved snapshot"
    : !connected
      ? "Reconnecting"
      : snapshot.state === "running"
        ? snapshot.last_packet_age === null
          ? "Listening"
          : snapshot.last_packet_age > 5
            ? "Listening · idle"
            : "Capturing"
        : snapshot.state === "error"
          ? "Capture error"
          : snapshot.state === "stopped"
            ? "Capture stopped"
            : snapshot.state === "starting"
              ? "Connecting adapter"
              : snapshot.state === "stopping"
                ? "Stopping"
                : "Ready to capture";

  const enterConsole = () => {
    setView("dashboard");
    window.location.hash = "console";
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const backToLanding = () => {
    setView("landing");
    window.location.hash = "home";
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (view === "landing") {
    return <LandingPage onEnterConsole={enterConsole} connected={connected} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            backToLanding();
          }}
          title="Return to Landing Page"
        >
          <span className="brand-mark">
            <Activity size={23} strokeWidth={2.5} />
          </span>
          NetSense<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">NETWORK WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              aria-label={label}
              className={`nav-item ${page === id ? "active" : ""}`}
              onClick={() => {
                setPage(id);
                if (id === "sessions") void loadSessions();
              }}
              aria-current={page === id ? "page" : undefined}
            >
              <Icon size={18} />
              <span>{label}</span>
              {id === "sessions" && (
                <span className="nav-count">{sessions.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <ShieldCheck size={19} />
            <div>
              <strong>Local by design</strong>
              <p>Your capture stays on this computer.</p>
            </div>
          </div>
          <div className="workspace-user">
            <span className="avatar">N</span>
            <div>
              <strong>Local workspace</strong>
              <small>IPv4 + IPv6 capture</small>
            </div>
            <span className={`dot ${connected ? "green" : ""}`} />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <button
              type="button"
              className="back-to-landing-btn"
              onClick={backToLanding}
              title="Return to Landing Page"
            >
              <ArrowLeft size={14} />
              <span>Landing page</span>
            </button>
            <div className="breadcrumb">
              Workspace <span>/</span>
              <strong>{pageNames[page]}</strong>
            </div>
          </div>
          <div className="backend-status">
            <span className={`dot ${connected ? "green" : ""}`} />
            {connected
              ? "Connected to capture service"
              : "Connecting to capture service"}
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="tiny-line" /> NETWORK INTELLIGENCE
              </div>
              <h1>
                {pageNames[page]}
                <span>.</span>
              </h1>
              <p>
                {page === "overview"
                  ? "Understand what’s moving through your network, as it happens."
                  : page === "investigate"
                    ? "Follow a connection. Inspect the packets. Find the details that matter."
                    : page === "sessions"
                      ? "Pick up where you left off. Your captured moments, kept locally."
                      : "Explore estimates from your trained traffic model."}
              </p>
            </div>
            <div className="heading-badge">
              <Globe2 size={15} /> ON YOUR DEVICE
            </div>
          </div>
          {!connected && (
            <div className="notice warning" role="status">
              <RefreshCw size={17} />
              <span>
                Live updates disconnected. Reconnecting automatically; displayed
                live data may be stale.
              </span>
            </div>
          )}
          {error && (
            <div role="alert" className="notice error">
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="notice success">
              <Check size={17} />
              <span>{notice}</span>
              <button
                className="icon-button"
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {saved && (
            <div className="saved-banner">
              <FolderClock size={18} />
              <div>
                <strong>{snapshot.session_name}</strong>
                <span>
                  Historical snapshot ·{" "}
                  {snapshot.saved_at && utc(snapshot.saved_at)} ?{" "}
                  {snapshot.interface}
                  {active ? " · Live capture continues in the background" : ""}
                </span>
              </div>
              <button className="button small" onClick={() => setSaved(null)}>
                Return to live <ArrowRight size={14} />
              </button>
            </div>
          )}
          <section className="capture-bar" aria-label="Capture controls">
            <div className="adapter-select">
              <Radio size={19} />
              <label>
                NETWORK ADAPTER
                <select
                  aria-label="Network adapter"
                  value={active ? (live?.interface ?? adapter) : adapter}
                  disabled={active || !!saved || adaptersLoading}
                  onChange={(e) => setAdapter(e.target.value)}
                >
                  {!adapters.length && (
                    <option value="">
                      {adaptersLoading
                        ? "Finding network adapters..."
                        : "No adapters available"}
                    </option>
                  )}
                  {adapters.map((a) => (
                    <option value={a.id} key={a.id}>
                      {a.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="capture-actions">
              <button
                className="button"
                disabled={
                  !!busy || !!saved || !connected || !live?.packets.length
                }
                onClick={openSave}
              >
                <Save size={16} /> Save session
              </button>
              {active ? (
                <button
                  className="button stop"
                  disabled={!!busy || !connected || live?.state === "stopping"}
                  onClick={() =>
                    void action("stop", async () => {
                      await request("/capture/stop", "POST");
                    })
                  }
                >
                  {busy === "stop" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Square size={13} />
                  )}{" "}
                  Stop capture
                </button>
              ) : (
                <button
                  className="button primary"
                  disabled={!!busy || !connected || !adapter || !!saved}
                  onClick={() =>
                    void action("start", async () => {
                      await request("/capture/start", "POST", {
                        interface: adapter,
                      });
                    })
                  }
                >
                  {busy === "start" ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    <Play size={15} fill="currentColor" />
                  )}{" "}
                  Start capture
                </button>
              )}
            </div>
          </section>
          {adapterError && (
            <div className="notice warning">
              <span>{adapterError}</span>
              <button
                className="text-button"
                onClick={() => void loadAdapters()}
              >
                Retry
              </button>
            </div>
          )}
          {!saved && snapshot.error && (
            <div role="alert" className="notice error">
              Capture failed: {snapshot.error}. Check Npcap and adapter
              permissions.
            </div>
          )}
          <div className="status-row">
            <span
              className={`capture-status ${!saved && connected && active ? "is-live" : ""}`}
            >
              <span className="dot" />
              {status}
            </span>
            <span>
              <Clock3 size={13} />
              {Math.floor(snapshot.elapsed / 60)
                .toString()
                .padStart(2, "0")}
              :
              {Math.floor(snapshot.elapsed % 60)
                .toString()
                .padStart(2, "0")}
              <span className="status-divider">/</span>
              {snapshot.packet_count.toLocaleString()} packets observed
            </span>
          </div>
          {(page === "overview" || page === "investigate") && (
            <div className="metrics-grid">
              <Metric
                label="Captured packets"
                value={
                  live || saved ? snapshot.packet_count.toLocaleString() : "—"
                }
                note="All IP packets this session"
                icon={Layers}
              />
              <Metric
                label="Captured volume"
                value={live || saved ? bytes(snapshot.byte_count) : "—"}
                note="Includes captured headers"
                icon={Database}
              />
              <Metric
                label="Packet rate"
                value={
                  !stale && snapshot.packet_rate !== null
                    ? snapshot.packet_rate.toFixed(1)
                    : "—"
                }
                unit="pkt/s"
                note="Recent observed average"
                icon={Activity}
              />
              <Metric
                label="Throughput"
                value={
                  !stale && snapshot.byte_rate !== null
                    ? ((snapshot.byte_rate * 8) / 1e6).toFixed(3)
                    : "—"
                }
                unit="Mbit/s"
                note="Traffic visible to this adapter"
                icon={ArrowUpRight}
              />
            </div>
          )}
          {page === "overview" && (
            <>
              <div className="overview-grid">
                <Chart history={snapshot.history} />
                <section className="panel protocol-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Protocol breakdown</h2>
                      <p>All packets this session</p>
                    </div>
                    <Layers size={17} className="muted" />
                  </div>
                  {snapshot.packet_count ? (
                    <div className="protocol-body">
                      <div className="protocol-total">
                        <strong>
                          {Object.keys(snapshot.protocols).length}
                        </strong>
                        <span>observed protocols</span>
                      </div>
                      <div className="protocol-strip">
                        {Object.entries(snapshot.protocols).map(
                          ([p, count]) => (
                            <span
                              key={p}
                              className={p.toLowerCase()}
                              style={{ flex: count }}
                              title={`${p}: ${count}`}
                            />
                          ),
                        )}
                      </div>
                      {Object.entries(snapshot.protocols)
                        .sort((a, b) => b[1] - a[1])
                        .map(([p, count]) => (
                          <div className="protocol-row" key={p}>
                            <span className={`legend-dot ${p.toLowerCase()}`} />
                            <strong>{p}</strong>
                            <span>{count.toLocaleString()}</span>
                            <em>
                              {((count / snapshot.packet_count) * 100).toFixed(
                                1,
                              )}
                              %
                            </em>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="empty">
                      <Layers size={30} />
                      <h3>No protocols yet</h3>
                      <p>Protocol counts appear as packets arrive.</p>
                    </div>
                  )}
                  <div className="panel-foot">
                    <ShieldCheck size={14} /> Measured from packet headers
                  </div>
                </section>
              </div>
              <section className="panel talker-preview">
                <div className="panel-heading">
                  <div>
                    <h2>Top talkers</h2>
                    <p>Most active endpoints in the retained packet window</p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setPage("investigate")}
                  >
                    Explore traffic <ArrowRight size={15} />
                  </button>
                </div>
                {summary.talkers.length ? (
                  <div className="talker-list">
                    {summary.talkers.slice(0, 5).map((t, i) => (
                      <div className="talker-preview-row" key={t.address}>
                        <span className="rank">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <span className="mono">{t.address}</span>
                        <div className="mini-bar">
                          <i
                            style={{
                              width: `${((t.sent + t.received) / (summary.talkers[0].sent + summary.talkers[0].received)) * 100}%`,
                            }}
                          />
                        </div>
                        <strong>{bytes(t.sent + t.received)}</strong>
                        <span>{t.packets.toLocaleString()} packets</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty compact">
                    <Network size={25} />
                    <p>
                      Your busiest endpoints will appear here once capture
                      begins.
                    </p>
                  </div>
                )}
              </section>
              <div className="scope-note">
                <CircleHelp size={15} />
                <span>
                  Investigation covers up to 2,000 recent packets. Rates average
                  up to five complete observed seconds. Throughput is observed
                  traffic, not your internet plan speed.
                </span>
              </div>
            </>
          )}
          {page === "investigate" && (
            <Investigation key={scope} snapshot={snapshot} />
          )}
          {page === "sessions" && (
            <section className="panel library">
              <div className="panel-heading">
                <div>
                  <h2>
                    Capture library{" "}
                    <span className="count-badge">{sessions.length} / 50</span>
                  </h2>
                  <p>
                    Session totals, recent packet headers, and chart history
                  </p>
                </div>
                <button
                  className="button small"
                  onClick={() => void loadSessions()}
                >
                  <RefreshCw size={15} /> Refresh
                </button>
              </div>
              {libraryError && (
                <div role="alert" className="notice error">
                  {libraryError}
                </div>
              )}
              {sessions.length ? (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Session</th>
                        <th>Saved at</th>
                        <th>Captured</th>
                        <th>Retained</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((session) => (
                        <tr key={session.id}>
                          <td>
                            <div className="session-title">
                              <span className="session-icon">
                                <FolderClock size={18} />
                              </span>
                              <strong>{session.name}</strong>
                            </div>
                          </td>
                          <td>{utc(session.saved_at)}</td>
                          <td>{session.packet_count.toLocaleString()}</td>
                          <td>{session.retained_count.toLocaleString()}</td>
                          <td>
                            <div className="row-actions">
                              <button
                                className="button small"
                                disabled={!!busy}
                                onClick={() => void openSession(session)}
                              >
                                Open <ArrowRight size={14} />
                              </button>
                              <button
                                className="icon-button danger"
                                disabled={!!busy}
                                title={`Delete ${session.name}`}
                                aria-label={`Delete ${session.name}`}
                                onClick={() => setDialog(session)}
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                !libraryError && (
                  <div className="empty">
                    <FolderClock size={35} />
                    <h3>A place for your investigations</h3>
                    <p>
                      Start a capture, then save a session to revisit it here.
                    </p>
                    <button
                      className="button"
                      onClick={() => {
                        setSaved(null);
                        setPage("overview");
                      }}
                    >
                      Go to live overview <ArrowRight size={15} />
                    </button>
                  </div>
                )
              )}
              <div className="panel-foot">
                Up to 2,000 headers and 60 seconds of chart history per snapshot
                · Nothing is automatically deleted
              </div>
            </section>
          )}
          {page === "model" && (
            <section className="panel model-panel">
              <div className="model-icon">
                <BrainCircuit size={30} />
              </div>
              <div className="eyebrow">OPTIONAL ANALYSIS</div>
              <h2>Traffic model estimates</h2>
              <p>{model.detail}</p>
              <p className="micro">
                The current model predicts Low, Medium, or High Traffic from
                packet-size sequences. These estimates do not establish
                congestion, packet loss, or malicious activity.
              </p>
              <button
                className="button primary"
                disabled={
                  !model.available ||
                  !!busy ||
                  snapshot.packets.length < 11 ||
                  (!saved && !connected)
                }
                onClick={() =>
                  void action("predict", async () => {
                    const result = await request<
                      Omit<NonNullable<typeof prediction>, "scope">
                    >("/model/predict", "POST", {
                      session_id: saved?.id ?? null,
                    });
                    setPrediction({ ...result, scope });
                  })
                }
              >
                {busy === "predict" ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <BrainCircuit size={16} />
                )}{" "}
                Analyze latest packet window
              </button>
              {model.available && snapshot.packets.length < 11 && (
                <p className="micro">
                  At least 11 retained packets are needed.
                </p>
              )}
              {prediction?.scope === scope && (
                <div className="prediction">
                  <h3>{prediction.label}</h3>
                  <p className="micro">
                    One-time estimate at{" "}
                    {prediction.packet_count.toLocaleString()} captured packets.
                    Run again to update.
                  </p>
                  {Object.entries(prediction.probabilities).map(
                    ([label, probability]) => (
                      <div className="probability" key={label}>
                        <span>{label}</span>
                        <progress value={probability} max={1} />
                        <strong>{(probability * 100).toFixed(1)}%</strong>
                      </div>
                    ),
                  )}
                </div>
              )}
            </section>
          )}
          <footer className="footer">
            <span>
              <span className="dot green" /> REAL PACKETS. LOCAL INSIGHT.
            </span>
            <span>
              NetSense <span className="muted">/</span> Network intelligence
            </span>
          </footer>
        </main>
      </div>
      {dialog && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget && !busy) setDialog(null);
          }}
        >
          <dialog
            open
            aria-modal="true"
            aria-labelledby="dialog-title"
            className="modal"
            onKeyDown={(e) => {
              if (e.key !== "Tab") return;
              const elements = [
                ...e.currentTarget.querySelectorAll<HTMLElement>(
                  "button:not(:disabled), input",
                ),
              ];
              if (e.shiftKey && document.activeElement === elements[0]) {
                e.preventDefault();
                elements.at(-1)?.focus();
              }
              if (!e.shiftKey && document.activeElement === elements.at(-1)) {
                e.preventDefault();
                elements[0]?.focus();
              }
            }}
          >
            <div className="panel-heading">
              <h2 id="dialog-title">
                {dialog === "save"
                  ? "Save this capture"
                  : "Delete saved session?"}
              </h2>
              <button
                className="icon-button"
                disabled={!!busy}
                aria-label="Close dialog"
                onClick={() => setDialog(null)}
              >
                <X size={18} />
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void action(dialog === "save" ? "save" : "delete", async () => {
                  if (dialog === "save") {
                    await request("/sessions", "POST", { name: name.trim() });
                    setNotice(
                      "Session saved. Find it in your capture library.",
                    );
                  } else {
                    await request(`/sessions/${dialog.id}`, "DELETE");
                    if (saved?.id === dialog.id) setSaved(null);
                    setNotice("Saved session deleted.");
                  }
                  setDialog(null);
                  await loadSessions();
                });
              }}
            >
              {dialog === "save" ? (
                <>
                  <label>
                    Session name
                    <input
                      autoFocus
                      required
                      maxLength={80}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Give this investigation a name"
                    />
                  </label>
                  <p>
                    Save full-session totals, up to 2,000 recent headers, and
                    the latest chart history on this computer.
                  </p>
                </>
              ) : (
                <p>
                  Permanently delete <strong>{dialog.name}</strong>? This cannot
                  be undone.
                </p>
              )}
              {error && (
                <p role="alert" className="modal-error">
                  {error}
                </p>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="button"
                  disabled={!!busy}
                  autoFocus={dialog !== "save"}
                  onClick={() => setDialog(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`button ${dialog === "save" ? "primary" : "delete-button"}`}
                  disabled={!!busy || (dialog === "save" && !name.trim())}
                >
                  {busy ? (
                    <LoaderCircle className="spin" size={15} />
                  ) : dialog === "save" ? (
                    <ArrowDownToLine size={16} />
                  ) : (
                    <Trash2 size={16} />
                  )}
                  {dialog === "save" ? "Save snapshot" : "Delete session"}
                </button>
              </div>
            </form>
          </dialog>
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  unit,
  note,
  icon: Icon,
}: {
  label: string;
  value: string;
  unit?: string;
  note: string;
  icon: LucideIcon;
}) {
  return (
    <section className="metric">
      <div className="metric-label">
        {label}
        <Icon size={17} />
      </div>
      <div className="metric-value">
        {value}
        <span>{value === "—" ? "" : unit}</span>
      </div>
      <p>{note}</p>
    </section>
  );
}

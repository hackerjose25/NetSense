import { useEffect, useState } from "react";
import { BrainCircuit, Download, LoaderCircle, RefreshCw } from "lucide-react";
import { request } from "../lib/api";
import { bytes } from "../lib/analysis";
import type { Session, Snapshot } from "../types";
import "../styles/model-analysis.css";

interface ModelStatus {
  available: boolean;
  detail: string;
  setup_command?: string;
  metadata: {
    version: string;
    trained_at: string;
    accuracy: number;
    macro_f1: number;
    test_windows: number;
    limitation: string;
  } | null;
}
interface Analysis {
  label: string;
  probabilities: Record<string, number>;
  distribution: Record<string, number>;
  packet_count: number;
  retained_packets: number;
  windows_analyzed: number;
  total_windows: number;
  windows: { start: number; end: number; label: string; probability: number }[];
  model_version: string;
  analyzed_at: string;
  source: string;
  warning: string;
  observed: {
    bytes: number;
    duration_seconds: number;
    packets_per_second: number | null;
  };
}

export default function ModelAnalysis({
  snapshot,
  sessionId,
  sessions,
  connected,
  onSelectSession,
}: {
  snapshot: Snapshot;
  sessionId: string | null;
  sessions: Session[];
  connected: boolean;
  onSelectSession: (id: string | null) => Promise<void>;
}) {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [result, setResult] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(0);
  const scope = sessionId ?? snapshot.capture_id ?? "live";
  useEffect(() => {
    setResult(null);
    setError("");
    setPage(0);
  }, [scope]);
  async function refresh() {
    try {
      setStatus(await request<ModelStatus>("/model"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void refresh();
  }, [connected]);
  async function analyze() {
    setBusy(true);
    setError("");
    try {
      setResult(
        await request<Analysis>("/model/predict", "POST", {
          session_id: sessionId,
        }),
      );
      setPage(0);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const enough = snapshot.packets.length >= 10;
  return (
    <div className="model-analysis">
      <section className="panel model-setup">
        <div className="panel-heading">
          <div>
            <h2>
              <BrainCircuit size={19} /> Packet-size pattern analysis
            </h2>
            <p>Analyze the retained capture with a trained LSTM classifier.</p>
          </div>
          <button
            className="button small"
            onClick={() => void refresh()}
            disabled={busy}
          >
            <RefreshCw size={15} /> Refresh model
          </button>
        </div>
        <div className="model-content">
          <div
            className={`notice ${status?.available ? "success" : "warning"}`}
            role="status"
          >
            {status?.detail ?? "Checking model readiness…"}
          </div>
          {!status?.available && status?.setup_command && (
            <div className="model-setup-command">
              <p>
                Train a matched model and scaler using the included dataset,
                then refresh:
              </p>
              <code>{status.setup_command}</code>
            </div>
          )}
          <label>
            Capture to analyze
            <select
              aria-label="Capture to analyze"
              value={sessionId ?? "live"}
              disabled={busy}
              onChange={(e) => {
                setBusy(true);
                setError("");
                void onSelectSession(
                  e.target.value === "live" ? null : e.target.value,
                )
                  .catch((e) => setError((e as Error).message))
                  .finally(() => setBusy(false));
              }}
            >
              <option value="live">Current live / stopped capture</option>
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} · {s.retained_count} retained packets
                </option>
              ))}
            </select>
          </label>
          <div className="model-action-row">
            <button
              className="button primary"
              onClick={() => void analyze()}
              disabled={
                busy ||
                !status?.available ||
                !enough ||
                (!sessionId && !connected)
              }
            >
              {busy ? (
                <LoaderCircle className="spin" size={16} />
              ) : (
                <BrainCircuit size={16} />
              )}
              {busy ? "Analyzing…" : "Analyze capture"}
            </button>
            <span className="micro">
              {snapshot.packets.length.toLocaleString()} retained packets ·{" "}
              {enough
                ? "Ready to analyze"
                : "Capture at least 10 packets or choose a saved session"}
            </span>
          </div>
          {error && (
            <div role="alert" className="notice error">
              {error}
            </div>
          )}
          <p className="micro">
            Low, Medium, and High Traffic are classes derived from packet-size
            thresholds in the training data. They do not measure congestion,
            packet loss, or malicious activity.
          </p>
        </div>
      </section>
      {result && (
        <>
          <div className="model-result-heading">
            <div>
              <h2>Analysis results</h2>
              <p>
                {result.source} ·{" "}
                {new Date(result.analyzed_at).toLocaleString()} ·{" "}
                {result.model_version}
              </p>
            </div>
            <button
              className="button small"
              onClick={() => {
                const url = URL.createObjectURL(
                  new Blob([JSON.stringify(result, null, 2)], {
                    type: "application/json",
                  }),
                );
                const link = document.createElement("a");
                link.href = url;
                link.download = "netsense_model_analysis.json";
                link.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
              }}
            >
              <Download size={15} /> Download report
            </button>
          </div>
          <div className="metrics-grid model-results">
            <section className="metric">
              <div className="metric-label">Most frequent class</div>
              <div className="model-class">{result.label}</div>
              <p>Across analyzed 10-packet windows</p>
            </section>
            <section className="metric">
              <div className="metric-label">Windows analyzed</div>
              <div className="metric-value">{result.windows_analyzed}</div>
              <p>
                Sampled across {result.total_windows.toLocaleString()} available
                windows
              </p>
            </section>
            <section className="metric">
              <div className="metric-label">Packets analyzed</div>
              <div className="metric-value">
                {result.retained_packets.toLocaleString()}
              </div>
              <p>
                Of {result.packet_count.toLocaleString()} captured this session
              </p>
            </section>
            <section className="metric">
              <div className="metric-label">Observed volume</div>
              <div className="metric-value">{bytes(result.observed.bytes)}</div>
              <p>Retained packet headers included</p>
            </section>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Class distribution</h2>
                <p>Window counts and mean model probabilities</p>
              </div>
            </div>
            <div className="model-distribution">
              {Object.entries(result.distribution).map(([label, count]) => (
                <div key={label}>
                  <strong>{label}</strong>
                  <progress max={result.windows_analyzed} value={count} />
                  <span>{count} windows</span>
                  <span>
                    {(result.probabilities[label] * 100).toFixed(1)}% mean
                    probability
                  </span>
                </div>
              ))}
            </div>
            <div className="panel-foot">{result.warning}</div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Window-by-window results</h2>
                <p>
                  Evenly sampled through the retained capture · UTC timestamps
                </p>
              </div>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Window start (UTC)</th>
                    <th>Window end (UTC)</th>
                    <th>Estimated class</th>
                    <th>Model probability</th>
                  </tr>
                </thead>
                <tbody>
                  {result.windows
                    .slice(page * 15, page * 15 + 15)
                    .map((w, i) => (
                      <tr key={i}>
                        <td className="mono">
                          {new Date(w.start * 1000).toISOString()}
                        </td>
                        <td className="mono">
                          {new Date(w.end * 1000).toISOString()}
                        </td>
                        <td>{w.label}</td>
                        <td>{(w.probability * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <div className="panel-foot">
              <span>Snapshot result; run analysis again to update.</span>
              <div className="pagination">
                <button
                  className="button small"
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </button>
                <span>
                  {page + 1} / {Math.ceil(result.windows.length / 15)}
                </span>
                <button
                  className="button small"
                  disabled={(page + 1) * 15 >= result.windows.length}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </section>
        </>
      )}
      {status?.metadata && (
        <section className="panel model-validation">
          <div className="panel-heading">
            <div>
              <h2>Training evaluation</h2>
              <p>Chronological holdout · Derived packet-size labels</p>
            </div>
          </div>
          <div className="model-content">
            <div className="validation-values">
              <span>
                Test accuracy{" "}
                <strong>{(status.metadata.accuracy * 100).toFixed(1)}%</strong>
              </span>
              <span>
                Macro-F1 <strong>{status.metadata.macro_f1.toFixed(3)}</strong>
              </span>
              <span>
                Test windows{" "}
                <strong>{status.metadata.test_windows.toLocaleString()}</strong>
              </span>
            </div>
            <p className="micro">
              {status.metadata.limitation} Probabilities have not been
              calibrated.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

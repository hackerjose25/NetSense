import { useState } from "react";
import { Activity } from "lucide-react";
import type { Snapshot } from "../types";

export default function Chart({ history }: { history: Snapshot["history"] }) {
  const [metric, setMetric] = useState<"Packets/s" | "Bytes/s">("Bytes/s");
  const [hover, setHover] = useState<number | null>(null);
  const values = history.map((row) =>
    metric === "Bytes/s" ? (row[metric] * 8) / 1e6 : row[metric],
  );
  const max = Math.max(...values, metric === "Bytes/s" ? 0.001 : 1) * 1.15;
  const x = (i: number) => 54 + (i * 700) / Math.max(1, values.length - 1);
  const y = (v: number) => 210 - (v / max) * 180;
  const line = values
    .map((v, i) => `${i ? "L" : "M"}${x(i)},${y(v)}`)
    .join(" ");
  const point = hover === null ? undefined : history[hover];
  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <div>
          <h2>Traffic activity</h2>
          <p>Last 60 observed seconds</p>
        </div>
        <div className="segmented" aria-label="Chart metric">
          <button
            className={metric === "Bytes/s" ? "selected" : ""}
            onClick={() => setMetric("Bytes/s")}
          >
            Throughput
          </button>
          <button
            className={metric === "Packets/s" ? "selected" : ""}
            onClick={() => setMetric("Packets/s")}
          >
            Packets/s
          </button>
        </div>
      </div>
      {history.length ? (
        <>
          <div className="chart-readout">
            {point
              ? `${point["Second since start"]}s · ${values[hover!].toFixed(metric === "Bytes/s" ? 3 : 0)}`
              : "Observed rate"}{" "}
            <span>{metric === "Bytes/s" ? "Mbit/s" : "packets/s"}</span>
          </div>
          <svg
            className="traffic-chart"
            viewBox="0 0 780 245"
            role="img"
            aria-label={`${metric === "Bytes/s" ? "Throughput" : "Packet rate"} over the last ${history.length} observed seconds`}
            onMouseLeave={() => setHover(null)}
            onMouseMove={(event) => {
              const rect = event.currentTarget.getBoundingClientRect();
              setHover(
                Math.max(
                  0,
                  Math.min(
                    history.length - 1,
                    Math.round(
                      ((((event.clientX - rect.left) / rect.width) * 780 - 54) /
                        700) *
                        (history.length - 1),
                    ),
                  ),
                ),
              );
            }}
          >
            <defs>
              <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
                <stop stopColor="#b8f36c" stopOpacity=".2" />
                <stop offset="1" stopColor="#b8f36c" stopOpacity="0" />
              </linearGradient>
            </defs>
            {[0, 1, 2, 3].map((step) => (
              <g key={step}>
                <line
                  x1="54"
                  x2="754"
                  y1={y((max * step) / 3)}
                  y2={y((max * step) / 3)}
                  className="grid-line"
                />
                <text x="43" y={y((max * step) / 3) + 4} textAnchor="end">
                  {((max * step) / 3).toFixed(metric === "Bytes/s" ? 3 : 0)}
                </text>
              </g>
            ))}
            <path
              d={`${line} L${x(values.length - 1)},210 L54,210 Z`}
              fill="url(#chart-fill)"
            />
            <path
              d={line}
              fill="none"
              stroke="#b8f36c"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
            {history.length === 1 && (
              <circle cx={x(0)} cy={y(values[0])} r="3" fill="#b8f36c" />
            )}
            <text x="54" y="236">
              {history[0]["Second since start"]}s
            </text>
            <text x="754" y="236" textAnchor="end">
              {history.at(-1)!["Second since start"]}s
            </text>
            {point && (
              <>
                <line
                  x1={x(hover!)}
                  x2={x(hover!)}
                  y1="20"
                  y2="210"
                  stroke="#657260"
                  strokeDasharray="4"
                />
                <circle
                  cx={x(hover!)}
                  cy={y(values[hover!])}
                  r="4"
                  fill="#b8f36c"
                />
              </>
            )}
          </svg>
        </>
      ) : (
        <div className="empty chart-empty">
          <Activity size={32} />
          <h3>Waiting for traffic</h3>
          <p>Start a capture to see real activity from your adapter.</p>
        </div>
      )}
      <div className="panel-foot">
        <span className="legend-dot" /> Captured traffic{" "}
        <span className="push">
          Complete one-second intervals · Idle periods count as zero
        </span>
      </div>
    </section>
  );
}

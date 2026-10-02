import { useMemo, useState } from "react";
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Download,
  Filter,
  Search,
  X,
} from "lucide-react";
import {
  aggregate,
  bytes,
  csv,
  defaultFilters,
  download,
  filterPackets,
  identity,
} from "../lib/analysis";
import type { Filters, Snapshot } from "../types";

export default function Investigation({ snapshot }: { snapshot: Snapshot }) {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [tab, setTab] = useState("Connections");
  const [selected, setSelected] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const result = useMemo(() => {
    try {
      return { packets: filterPackets(snapshot.packets, filters), error: "" };
    } catch (error) {
      return { packets: [], error: (error as Error).message };
    }
  }, [snapshot.packets, filters]);
  const { flows, talkers } = useMemo(
    () => aggregate(result.packets),
    [result.packets],
  );
  const packets = useMemo(
    () =>
      [
        ...(selected
          ? result.packets.filter((p) => identity(p).id === selected)
          : result.packets),
      ].reverse(),
    [result.packets, selected],
  );
  const change = (key: keyof Filters, value: string | number) => {
    setFilters((old) => ({ ...old, [key]: value }));
    setPage(0);
  };
  const selectTab = (name: string) => {
    setTab(name);
    setPage(0);
  };
  const count =
    tab === "Connections"
      ? flows.length
      : tab === "Top talkers"
        ? talkers.length
        : packets.length;
  const pages = Math.max(1, Math.ceil(count / 50));
  const currentPage = Math.min(page, pages - 1);
  const start = currentPage * 50;
  const exportRows = () => {
    if (tab === "Connections")
      download(
        "netsense_connections.csv",
        csv(
          [
            "Protocol",
            "Endpoint A",
            "Endpoint B",
            "Packets",
            "Bytes",
            "A to B bytes",
            "B to A bytes",
            "Duration (s)",
          ],
          flows.map((f) => [
            f.protocol,
            f.a,
            f.b,
            f.packets,
            f.bytes,
            f.sent,
            f.received,
            f.last - f.first,
          ]),
        ),
      );
    else if (tab === "Top talkers")
      download(
        "netsense_top_talkers.csv",
        csv(
          [
            "IP address",
            "Sent bytes",
            "Received bytes",
            "Total bytes",
            "Packets",
          ],
          talkers.map((t) => [
            t.address,
            t.sent,
            t.received,
            t.sent + t.received,
            t.packets,
          ]),
        ),
      );
    else
      download(
        "netsense_packets.csv",
        csv(
          [
            "Timestamp (UTC)",
            "Source",
            "Source port",
            "Destination",
            "Destination port",
            "Protocol",
            "Length",
          ],
          packets.map((p) => [
            new Date(p.Timestamp * 1000).toISOString(),
            p.Source,
            p["Source port"],
            p.Destination,
            p["Destination port"],
            p.Protocol,
            p.Length,
          ]),
        ),
      );
  };
  return (
    <>
      <div className="scope-note">
        <Filter size={15} />
        <span>
          Investigating{" "}
          <strong>{snapshot.packets.length.toLocaleString()}</strong> retained
          packets of {snapshot.packet_count.toLocaleString()} captured. Session
          totals remain unfiltered.
        </span>
      </div>
      <section className="panel filters-panel">
        <label>
          Protocol
          <select
            value={filters.protocol}
            onChange={(e) => change("protocol", e.target.value)}
          >
            {["All", "TCP", "UDP", "OTHER"].map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </label>
        <label className="address-filter">
          IP address or subnet
          <input
            placeholder="Search an IP or CIDR subnet"
            value={filters.address}
            onChange={(e) => change("address", e.target.value)}
          />
        </label>
        <label>
          Port
          <input
            placeholder="e.g. 443"
            value={filters.port}
            onChange={(e) => change("port", e.target.value)}
            inputMode="numeric"
          />
        </label>
        <label>
          Time window
          <select
            value={filters.window}
            onChange={(e) => change("window", Number(e.target.value))}
          >
            <option value="0">All retained packets</option>
            {[10, 30, 60].map((s) => (
              <option value={s} key={s}>
                Last {s} seconds
              </option>
            ))}
          </select>
        </label>
        <button
          className="icon-button reset-filter"
          title="Clear filters"
          aria-label="Clear filters"
          onClick={() => {
            setFilters(defaultFilters);
            setSelected(null);
            setPage(0);
          }}
        >
          <X size={17} />
        </button>
      </section>
      <p className="micro">
        IP and port match either endpoint. Time windows end at the latest
        retained packet.
      </p>
      {result.error && (
        <div role="alert" className="notice error">
          {result.error}
        </div>
      )}
      <section className="panel investigation-panel">
        <div className="table-toolbar">
          <div className="tabs" role="tablist" aria-label="Investigation views">
            {["Connections", "Top talkers", "Packets"].map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={tab === name}
                className={tab === name ? "active" : ""}
                onClick={() => selectTab(name)}
              >
                {name}
              </button>
            ))}
          </div>
          <button
            className="button small"
            disabled={!count || !!result.error}
            onClick={exportRows}
          >
            <Download size={15} /> Export CSV
          </button>
        </div>
        <div className="table-description">
          {tab === "Connections"
            ? "Endpoint pairs ranked by bytes. Select a connection to inspect its packets. A/B indicate direction between endpoints."
            : tab === "Top talkers"
              ? "Endpoints ranked by sent + received bytes. Traffic contributes to both endpoints; totals across IPs count it twice."
              : "Captured headers, newest first. Timestamps are UTC. Exports include all matching packets."}
        </div>
        {tab === "Packets" && selected && (
          <div className="connection-focus">
            <span>Connection: {JSON.parse(selected).slice(1).join(" ↔ ")}</span>
            <button
              className="text-button"
              onClick={() => {
                setSelected(null);
                setPage(0);
              }}
            >
              Show all <X size={14} />
            </button>
          </div>
        )}
        {!count ? (
          <div className="empty">
            <Search size={30} />
            <h3>
              {snapshot.packets.length
                ? "No matching traffic"
                : "Your investigation starts here"}
            </h3>
            <p>
              {snapshot.packets.length
                ? "Adjust your filters or clear the selected connection."
                : "Start a capture or open a saved session to explore connections."}
            </p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {(tab === "Connections"
                    ? [
                        "Protocol",
                        "Endpoint A",
                        "Endpoint B",
                        "Packets",
                        "Bytes",
                        "A → B",
                        "B → A",
                        "Duration",
                        "",
                      ]
                    : tab === "Top talkers"
                      ? [
                          "IP address",
                          "Sent",
                          "Received",
                          "Total",
                          "Packets",
                          "",
                        ]
                      : [
                          "Time (UTC)",
                          "Source",
                          "Destination",
                          "Protocol",
                          "Size",
                        ]
                  ).map((h, i) => (
                    <th key={i}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tab === "Connections"
                  ? flows.slice(start, start + 50).map((f) => (
                      <tr key={f.id}>
                        <td>
                          <span
                            className={`protocol ${f.protocol.toLowerCase()}`}
                          >
                            {f.protocol}
                          </span>
                        </td>
                        <td className="mono">{f.a}</td>
                        <td className="mono">{f.b}</td>
                        <td>{f.packets.toLocaleString()}</td>
                        <td>{bytes(f.bytes)}</td>
                        <td>{bytes(f.sent)}</td>
                        <td>{bytes(f.received)}</td>
                        <td>{(f.last - f.first).toFixed(3)}s</td>
                        <td>
                          <button
                            className="icon-button"
                            aria-label={`Inspect ${f.a} to ${f.b}`}
                            title="Inspect packets"
                            onClick={() => {
                              setSelected(f.id);
                              selectTab("Packets");
                            }}
                          >
                            <ArrowRight size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  : tab === "Top talkers"
                    ? talkers.slice(start, start + 50).map((t) => (
                        <tr key={t.address}>
                          <td className="mono">{t.address}</td>
                          <td>{bytes(t.sent)}</td>
                          <td>{bytes(t.received)}</td>
                          <td>{bytes(t.sent + t.received)}</td>
                          <td>{t.packets.toLocaleString()}</td>
                          <td>
                            <button
                              className="icon-button"
                              aria-label={`Inspect ${t.address}`}
                              onClick={() => {
                                change("address", t.address);
                                setSelected(null);
                                selectTab("Packets");
                              }}
                            >
                              <ArrowRight size={16} />
                            </button>
                          </td>
                        </tr>
                      ))
                    : packets.slice(start, start + 50).map((p, i) => (
                        <tr key={`${start + i}-${p.Timestamp}`}>
                          <td
                            className="mono"
                            title={new Date(p.Timestamp * 1000).toISOString()}
                          >
                            {new Date(p.Timestamp * 1000)
                              .toISOString()
                              .slice(11, 23)}
                          </td>
                          <td className="mono">
                            {p.Source}
                            <span className="muted">
                              {p["Source port"] != null
                                ? ` : ${p["Source port"]}`
                                : ""}
                            </span>
                          </td>
                          <td className="mono">
                            {p.Destination}
                            <span className="muted">
                              {p["Destination port"] != null
                                ? ` : ${p["Destination port"]}`
                                : ""}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`protocol ${p.Protocol.toLowerCase()}`}
                            >
                              {p.Protocol}
                            </span>
                          </td>
                          <td>{bytes(p.Length)}</td>
                        </tr>
                      ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="panel-foot">
          <span>
            {count.toLocaleString()} matching {tab.toLowerCase()} · 50 per page
          </span>
          <div className="pagination">
            <button
              className="icon-button"
              aria-label="Previous page"
              disabled={currentPage === 0}
              onClick={() => setPage(currentPage - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            <span>
              {currentPage + 1} / {pages}
            </span>
            <button
              className="icon-button"
              aria-label="Next page"
              disabled={currentPage + 1 >= pages}
              onClick={() => setPage(currentPage + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </section>
      <p className="micro">
        Connection duration spans the first and last matching retained packets.
        Reused endpoint pairs are grouped together.
      </p>
    </>
  );
}

"""A live-only monitoring console. Every displayed metric comes from capture."""

from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from live_capture import LiveCapture


def empty_chart(title, description, icon="≋"):
    st.html(f'<div class="ns-chart-empty"><span class="ns-empty-icon" aria-hidden="true">{icon}</span>'
            f'<h4>{escape(title)}</h4><p>{escape(description)}</p></div>')


def panel_title(title, detail):
    st.html(f'<div class="ns-panel-title"><h3>{escape(title)}</h3><span>{escape(detail)}</span></div>')


def metrics(snapshot):
    available = snapshot["packet_count"] > 0 or (snapshot["state"] in {"running", "stopped"} and snapshot["elapsed"] > 0)
    values = [
        ("Captured packets", f"{snapshot['packet_count']:,}" if available else None, "", "All IP packets this session", "↗"),
        ("Captured volume", f"{snapshot['byte_count'] / 1000:,.1f}" if available else None, "KB", "Includes captured headers", "◫"),
        ("Packet rate", f"{snapshot['packet_rate']:,.1f}" if snapshot["packet_rate"] is not None else None, "pkt/s", "Recent observed average", "≋"),
        ("Throughput", f"{snapshot['byte_rate'] * 8 / 1_000_000:.3f}" if snapshot["byte_rate"] is not None else None, "Mbit/s", "Traffic visible to this adapter", "↗"),
    ]
    cards = []
    for label, value, unit, note, icon in values:
        cards.append(f'<div class="ns-metric"><div class="ns-metric-top">{label}<span class="ns-metric-icon" aria-hidden="true">{icon}</span></div>'
                     f'<div class="ns-metric-value {"unavailable" if value is None else ""}" aria-label="{label}: {value or "Unavailable"}">{value or "—"}'
                     f'<span class="ns-metric-unit">{unit if value is not None else ""}</span></div><div class="ns-metric-note">{note}</div></div>')
    st.html('<div class="ns-metrics">' + ''.join(cards) + '</div>')


def render_dashboard(load_model, predict, preprocess, make_sequences):
    if "live_capture_v2" not in st.session_state:
        st.session_state.live_capture_v2 = LiveCapture()
    capture = st.session_state.live_capture_v2

    with st.container(key="console"):
        st.html('''<section class="ns-section-head" id="monitoring"><div>
        <div class="ns-section-index">01 / LIVE MONITORING</div><h2>Your network. In focus.</h2>
        <p>Connect an adapter. See what’s happening, as it happens.</p></div>
        <span class="ns-section-label">LOCAL CAPTURE / REAL DATA</span></section>''')
        try:
            from scapy.all import conf
            adapters = {str(a.network_name): a.description or a.name for a in conf.ifaces.values()}
            default = str(conf.iface.network_name)
        except Exception as exc:
            st.error(f"Network interfaces unavailable: {exc}")
            return
        if not adapters:
            st.error("No capture interfaces found. Check the capture driver and permissions.")
            return

        @st.fragment(run_every=2)
        def show_measurements():
            snapshot = capture.snapshot()
            state = snapshot["state"]
            active = state in {"starting", "running", "stopping"}
            with st.container(key="capture_controls"):
                adapter_col, start_col, stop_col = st.columns([3.5, 1.25, 1])
                with adapter_col:
                    interface = st.selectbox("NETWORK ADAPTER", list(adapters),
                                             index=list(adapters).index(default) if default in adapters else 0,
                                             format_func=adapters.get, disabled=active, key="capture_adapter")
                with start_col:
                    if st.button("Start Live Capture", disabled=active, type="primary", width="stretch"):
                        capture.start(interface)
                        st.rerun()
                with stop_col:
                    if st.button("Stop Capture", disabled=not active, width="stretch"):
                        capture.stop()
                        st.rerun()

            age = snapshot["last_packet_age"]
            status_style = ""
            if state == "error":
                status, status_style = "CAPTURE UNAVAILABLE", "is-error"
                st.error(f"Capture failed: {snapshot['error']}")
                st.caption("Check Npcap and capture permissions on Windows, or packet capture privileges on Linux/macOS. Then start a new capture.")
            elif state == "starting":
                status = "CONNECTING TO YOUR ADAPTER"
            elif state == "running":
                if age is None:
                    status, status_style = "LISTENING · WAITING FOR IP PACKETS", "is-live"
                elif age > 5:
                    status, status_style = f"LISTENING · LAST PACKET {age:.0f}s AGO", "is-stale"
                else:
                    status, status_style = f"LIVE · LAST PACKET {age:.1f}s AGO", "is-live"
            elif state in {"stopped", "stopping"}:
                status = "CAPTURE STOPPED · SAVED SNAPSHOT"
            else:
                status = "READY TO CAPTURE"
            duration = f"{int(snapshot['elapsed']) // 60:02d}:{int(snapshot['elapsed']) % 60:02d}"
            st.html(f'<div class="ns-status {status_style}" role="status"><span class="ns-status-main"><i aria-hidden="true"></i>{status}</span>'
                    f'<span class="ns-status-meta">SESSION {duration} &nbsp; / &nbsp; IPv4 + IPv6</span></div>')
            metrics(snapshot)

            overview, explorer = st.tabs(["Traffic overview", "Packet explorer"])
            df = pd.DataFrame(snapshot["packets"])
            with overview:
                traffic, protocols = st.columns([2.15, 1], gap="large")
                with traffic:
                    panel_title("Traffic activity", "LAST 60 OBSERVED SECONDS")
                    if snapshot["history"]:
                        history = pd.DataFrame(snapshot["history"])
                        rate_choice = st.radio("Rate metric", ["Packet rate", "Throughput"], horizontal=True,
                                               label_visibility="collapsed", key="rate_metric")
                        column = "Packets/s" if rate_choice == "Packet rate" else "Mbit/s"
                        history["Mbit/s"] = history["Bytes/s"] * 8 / 1_000_000
                        chart = alt.Chart(history).mark_area(
                            line={"color": "#829cff", "strokeWidth": 2},
                            color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color="#829cff55", offset=0),
                                                                       alt.GradientStop(color="#829cff00", offset=1)], x1=1, x2=1, y1=0, y2=1),
                        ).encode(x=alt.X("Second since start:Q", title="Seconds since capture started"),
                                 y=alt.Y(f"{column}:Q", title=column, scale=alt.Scale(zero=True)),
                                 tooltip=["Second since start", column]).properties(height=230)
                        st.altair_chart(chart.configure_view(stroke=None).configure_axis(
                            gridColor="#232833", domainColor="#303747", labelColor="#7e899e", titleColor="#9da7b8"), width="stretch")
                    else:
                        empty_chart("Your traffic will appear here", "Start a capture to see live packet activity. No sample data is shown.")
                with protocols:
                    panel_title("Protocol distribution", "THIS SESSION")
                    if snapshot["protocols"]:
                        counts = pd.DataFrame([{"Protocol": k, "Packets": v} for k, v in snapshot["protocols"].items()])
                        chart = alt.Chart(counts).mark_bar(cornerRadiusEnd=3, size=22).encode(
                            x=alt.X("Packets:Q", title="Captured packets", axis=alt.Axis(tickMinStep=1)),
                            y=alt.Y("Protocol:N", title=None),
                            color=alt.Color("Protocol:N", scale=alt.Scale(domain=["TCP", "UDP", "OTHER"],
                                                                        range=["#829cff", "#c2f58a", "#697385"]), legend=None),
                            tooltip=["Protocol", "Packets"],
                        ).properties(height=230)
                        st.altair_chart(chart.configure_view(stroke=None).configure_axis(
                            gridColor="#232833", domainColor="#303747", labelColor="#7e899e", titleColor="#9da7b8"), width="stretch")
                    else:
                        empty_chart("Waiting for packets", "TCP, UDP, and other IP protocols will be counted as they arrive.", "◫")
                st.caption("Rates average up to five complete observed seconds. Idle intervals count as zero. Stopped sessions show historical observations; current rates are unavailable.")

            with explorer:
                panel_title("Packet explorer", "LATEST 100 PACKETS")
                if not df.empty:
                    display = df.tail(100).copy()
                    display["Timestamp"] = pd.to_datetime(display["Timestamp"], unit="s", utc=True)
                    st.dataframe(display, hide_index=True, width="stretch")
                    st.download_button("Export captured packets ↓", df.to_csv(index=False).encode("utf-8"),
                                       file_name="netsense_live_packets.csv", mime="text/csv")
                    st.caption(f"UTC timestamps · Export contains {len(df):,} recent packets (up to 2,000). Session totals include all captured packets.")
                else:
                    empty_chart("Every packet tells a story", "Start live capture to inspect timestamps, endpoints, protocols, and packet sizes.", "↗")

            with st.expander("Measurement details & optional AI analysis"):
                st.caption("Capture observes the computer running this app. A new capture clears the previous session. Throughput measures visible traffic, not internet plan speed. TCP congestion window, packet loss, and timeouts are not measured.")
                model_path = st.text_input("Model path", "tcp_udp_lstm_pytorch.pt", key="model_path")
                artifacts_exist = Path(model_path).is_file() and Path("scaler.pkl").is_file()
                use_ai = st.checkbox("Show model estimates", value=False, disabled=not artifacts_exist, key="use_ai")
                if not artifacts_exist:
                    st.caption("AI estimates are unavailable until trained weights and the matching scaler.pkl are supplied. All live measurements work independently.")
                if use_ai and artifacts_exist:
                    st.caption("AI classes are estimates from captured packet sizes, not measured congestion or packet loss.")
                    if len(df) <= 10:
                        st.info("Waiting for at least 11 captured packets for AI analysis.")
                    else:
                        try:
                            sequences, _ = make_sequences(preprocess(df.tail(11)), 10)
                            preds, probs = predict(load_model(model_path), sequences)
                            names = ["Low Traffic", "Medium Traffic", "High Traffic"]
                            st.write(f"Estimated class: **{names[int(preds[-1])]}**")
                            st.dataframe(pd.DataFrame([probs[-1]], columns=names), hide_index=True)
                        except Exception as exc:
                            st.error(f"AI estimate unavailable: {exc}")

        show_measurements()

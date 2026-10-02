import * as ipaddr from "ipaddr.js";
import type { Filters, Flow, Packet, Talker } from "../types";

export const defaultFilters: Filters = {
  protocol: "All",
  address: "",
  port: "",
  window: 0,
};
export function endpoint(address: string, port: number | null) {
  const host = address.includes(":") ? `[${address}]` : address;
  return port == null ? host : `${host}:${port}`;
}
export function identity(packet: Packet) {
  const [a, b] = [
    endpoint(packet.Source, packet["Source port"]),
    endpoint(packet.Destination, packet["Destination port"]),
  ].sort();
  return { id: JSON.stringify([packet.Protocol, a, b]), a, b };
}
export function filterPackets(packets: Packet[], filters: Filters) {
  const { protocol, address, port, window } = filters;
  let network: ReturnType<typeof ipaddr.parseCIDR> | undefined;
  if (address.trim()) {
    const value = address.trim();
    try {
      network = value.includes("/")
        ? ipaddr.parseCIDR(value)
        : ipaddr.parseCIDR(
            `${value}/${ipaddr.parse(value).kind() === "ipv4" ? 32 : 128}`,
          );
    } catch {
      throw new Error("Enter a valid IPv4/IPv6 address or CIDR subnet.");
    }
  }
  if (port.trim() && (!/^\d+$/.test(port.trim()) || Number(port) > 65535)) {
    throw new Error("Port must be a whole number from 0 to 65535.");
  }
  const latest = packets.reduce(
    (max, p) => Math.max(max, p.Timestamp),
    -Infinity,
  );
  const matches = (address: string) => {
    if (!network) return true;
    const parsed = ipaddr.parse(address);
    return (
      parsed.kind() === network[0].kind() &&
      (parsed as ipaddr.IPv4).match(network as [ipaddr.IPv4, number])
    );
  };
  return packets.filter(
    (p) =>
      (protocol === "All" || p.Protocol === protocol) &&
      (!network || matches(p.Source) || matches(p.Destination)) &&
      (!port.trim() ||
        p["Source port"] === Number(port) ||
        p["Destination port"] === Number(port)) &&
      (!window || p.Timestamp >= latest - window),
  );
}
export function aggregate(packets: Packet[]) {
  const flows = new Map<string, Flow>();
  const hosts = new Map<string, Talker>();
  for (const p of packets) {
    const { id, a, b } = identity(p);
    const flow = flows.get(id) ?? {
      id,
      a,
      b,
      protocol: p.Protocol,
      packets: 0,
      bytes: 0,
      sent: 0,
      received: 0,
      first: p.Timestamp,
      last: p.Timestamp,
    };
    flow.packets++;
    flow.bytes += p.Length;
    if (endpoint(p.Source, p["Source port"]) === a) flow.sent += p.Length;
    else flow.received += p.Length;
    flow.first = Math.min(flow.first, p.Timestamp);
    flow.last = Math.max(flow.last, p.Timestamp);
    flows.set(id, flow);
    for (const address of new Set([p.Source, p.Destination])) {
      const host = hosts.get(address) ?? {
        address,
        sent: 0,
        received: 0,
        packets: 0,
      };
      host.packets++;
      if (address === p.Source) host.sent += p.Length;
      if (address === p.Destination) host.received += p.Length;
      hosts.set(address, host);
    }
  }
  return {
    flows: [...flows.values()].sort(
      (a, b) => b.bytes - a.bytes || a.id.localeCompare(b.id),
    ),
    talkers: [...hosts.values()].sort(
      (a, b) =>
        b.sent + b.received - a.sent - a.received ||
        a.address.localeCompare(b.address),
    ),
  };
}
export function bytes(value: number) {
  if (value < 1000) return `${value.toLocaleString()} B`;
  const power = Math.min(Math.floor(Math.log10(value) / 3), 3);
  return `${(value / 1000 ** power).toLocaleString(undefined, { maximumFractionDigits: 1 })} ${["B", "KB", "MB", "GB"][power]}`;
}
export function csv(headers: string[], rows: unknown[][]) {
  const cell = (value: unknown) => {
    let text = String(value ?? "");
    if (/^[=+@\-\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [headers, ...rows].map((row) => row.map(cell).join(",")).join("\r\n");
}
export function download(name: string, content: string) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

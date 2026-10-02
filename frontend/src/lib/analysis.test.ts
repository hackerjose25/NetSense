import { describe, expect, it } from "vitest";
import {
  aggregate,
  csv,
  defaultFilters,
  filterPackets,
  identity,
} from "./analysis";
import type { Packet } from "../types";

const packets: Packet[] = [
  {
    Timestamp: 10,
    Length: 40,
    Protocol: "TCP",
    Source: "10.0.0.1",
    Destination: "10.0.0.2",
    "Source port": 5000,
    "Destination port": 443,
  },
  {
    Timestamp: 20,
    Length: 60,
    Protocol: "TCP",
    Source: "10.0.0.2",
    Destination: "10.0.0.1",
    "Source port": 443,
    "Destination port": 5000,
  },
  {
    Timestamp: 40,
    Length: 48,
    Protocol: "UDP",
    Source: "2001:db8::1",
    Destination: "2001:db8::2",
    "Source port": 53,
    "Destination port": 6000,
  },
];

describe("retained packet investigation", () => {
  it("groups both directions while retaining protocol and ports", () => {
    const { flows, talkers } = aggregate(packets);
    expect(flows).toHaveLength(2);
    expect(flows[0]).toMatchObject({
      packets: 2,
      bytes: 100,
      sent: 40,
      received: 60,
      first: 10,
      last: 20,
    });
    expect(identity(packets[0]).id).toBe(identity(packets[1]).id);
    expect(identity({ ...packets[0], Protocol: "UDP" }).id).not.toBe(
      identity(packets[0]).id,
    );
    expect(talkers[0]).toMatchObject({
      address: "10.0.0.1",
      sent: 40,
      received: 60,
      packets: 2,
    });
    expect(
      talkers.reduce((sum, host) => sum + host.sent + host.received, 0),
    ).toBe(296);
  });
  it("matches combined filters in either direction", () => {
    expect(
      filterPackets(packets, {
        protocol: "TCP",
        address: "10.0.0.0/24",
        port: "443",
        window: 0,
      }),
    ).toHaveLength(2);
    expect(
      filterPackets(packets, { ...defaultFilters, address: "10.0.0.10" }),
    ).toHaveLength(0);
    expect(
      filterPackets(packets, {
        ...defaultFilters,
        address: "2001:db8::/32",
        port: "53",
        window: 10,
      }),
    ).toHaveLength(1);
    expect(
      filterPackets(packets, {
        ...defaultFilters,
        address: "2001:0db8:0:0:0:0:0:2",
      }),
    ).toHaveLength(1);
    expect(
      filterPackets(packets, {
        ...defaultFilters,
        protocol: "TCP",
        window: 10,
      }),
    ).toHaveLength(0);
  });
  it("rejects invalid filters instead of silently ignoring them", () => {
    for (const port of ["65536", "-1", "1.5", "oops"])
      expect(() => filterPackets(packets, { ...defaultFilters, port })).toThrow(
        "Port",
      );
    expect(() =>
      filterPackets(packets, { ...defaultFilters, address: "bad-ip" }),
    ).toThrow("IPv4");
  });
  it("handles empty, non-transport and loopback packets", () => {
    expect(aggregate([])).toEqual({ flows: [], talkers: [] });
    const other = {
      ...packets[0],
      Protocol: "OTHER",
      "Source port": null,
      "Destination port": null,
    };
    expect(
      filterPackets([other], { ...defaultFilters, port: "0" }),
    ).toHaveLength(0);
    const { talkers } = aggregate([{ ...other, Destination: other.Source }]);
    expect(talkers).toEqual([
      { address: other.Source, sent: 40, received: 40, packets: 1 },
    ]);
  });
  it("exports CSV with escaping and spreadsheet formula protection", () => {
    expect(
      csv(
        ["IP", "Note"],
        [
          ["10.0.0.1", 'a,"b"'],
          ["::1", "=1+1"],
        ],
      ),
    ).toContain('"a,""b"""');
    expect(csv(["Note"], [["=1+1"]])).toContain('"\'=1+1"');
  });
});

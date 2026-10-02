export interface Packet {
  Timestamp: number;
  Length: number;
  Protocol: string;
  Source: string;
  Destination: string;
  "Source port": number | null;
  "Destination port": number | null;
}
export interface Snapshot {
  capture_id?: string;
  state: string;
  error: string | null;
  interface: string | null;
  packets: Packet[];
  packet_count: number;
  byte_count: number;
  elapsed: number;
  protocols: Record<string, number>;
  packet_rate: number | null;
  byte_rate: number | null;
  last_packet_age: number | null;
  history: {
    "Second since start": number;
    "Packets/s": number;
    "Bytes/s": number;
  }[];
  session_name?: string;
  saved_at?: string;
}
export interface Session {
  id: string;
  name: string;
  saved_at: string;
  packet_count: number;
  retained_count: number;
}
export interface Adapter {
  id: string;
  name: string;
}
export interface Filters {
  protocol: string;
  address: string;
  port: string;
  window: number;
}
export interface Flow {
  id: string;
  protocol: string;
  a: string;
  b: string;
  packets: number;
  bytes: number;
  sent: number;
  received: number;
  first: number;
  last: number;
}
export interface Talker {
  address: string;
  sent: number;
  received: number;
  packets: number;
}

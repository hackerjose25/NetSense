import { useEffect, useState } from "react";
import type { Snapshot } from "../types";

export function useLiveCapture() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | undefined;
    let timer: ReturnType<typeof setTimeout>;
    let watchdog: ReturnType<typeof setTimeout>;
    let failures = 0;
    function connect() {
      socket = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/live`,
      );
      const current = socket;
      const resetWatchdog = () => {
        clearTimeout(watchdog);
        watchdog = setTimeout(() => {
          setConnected(false);
          current.close();
        }, 15000);
      };
      resetWatchdog();
      current.onmessage = (event) => {
        if (cancelled) return;
        resetWatchdog();
        const next = JSON.parse(event.data) as Partial<Snapshot>;
        setSnapshot(
          (previous) =>
            ({
              ...next,
              packets: next.packets ?? previous?.packets ?? [],
            }) as Snapshot,
        );
        setConnected(true);
        failures = 0;
        current.send("ack");
      };
      current.onerror = () => current.close();
      current.onclose = () => {
        clearTimeout(watchdog);
        if (cancelled) return;
        setConnected(false);
        timer = setTimeout(connect, Math.min(1000 * 2 ** failures++, 10000));
      };
    }
    connect();
    return () => {
      cancelled = true;
      clearTimeout(timer);
      clearTimeout(watchdog);
      socket?.close();
    };
  }, []);
  return { snapshot, connected };
}

import { useEffect, useRef, useState } from "react";
import { Pause, Play } from "lucide-react";
import video from "../assets/console-network.mp4";
import poster from "../assets/console-network.jpg";
import "../styles/console-glass.css";

export default function ConsoleBackground() {
  const ref = useRef<HTMLVideoElement>(null);
  const [paused, setPaused] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setPaused(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const sync = () => {
      if (paused || document.hidden) element.pause();
      else void element.play().catch(() => setPaused(true));
    };
    sync();
    document.addEventListener("visibilitychange", sync);
    return () => document.removeEventListener("visibilitychange", sync);
  }, [paused]);
  return <>
    <div className="console-backdrop" aria-hidden="true" style={{ backgroundImage: `url(${poster})` }}>
      <video ref={ref} src={video} poster={poster} muted loop playsInline preload="metadata" onError={() => { setFailed(true); setPaused(true); }} />
      <div className="console-backdrop-shade" />
    </div>
    <button className="console-motion button small" disabled={failed} onClick={() => setPaused(!paused)} aria-label={paused ? "Play console background" : "Pause console background"}>
      {paused ? <Play size={13} /> : <Pause size={13} />}
      <span>{failed ? "Static background" : paused ? "Play background" : "Pause background"}</span>
    </button>
  </>;
}

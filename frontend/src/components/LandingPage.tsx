import React, { useRef, useState } from "react";
import {
  Activity,
  ArrowDown,
  ArrowUpRight,
  ExternalLink,
  Layers,
  Network,
  Pause,
  Play,
  Radio,
  ShieldCheck,
} from "lucide-react";
import heroVideo from "../assets/hero-network.mp4";
import heroPoster from "../assets/hero-poster.jpg";
import joseAvatar from "../assets/jose.jpg";
import gayathriAvatar from "../assets/gayathri.jpg";

interface LandingPageProps {
  onEnterConsole: () => void;
  connected: boolean;
}

export default function LandingPage({ onEnterConsole, connected }: LandingPageProps) {
  const [isPlaying, setIsPlaying] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const toggleVideo = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      void videoRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="landing-container">
      {/* ─── Top Navigation Bar ─── */}
      <header className="landing-nav" aria-label="Landing navigation">
        <a href="#home" className="landing-brand">
          <span className="brand-mark">
            <Activity size={22} strokeWidth={2.5} />
          </span>
          NetSense<span className="brand-dot">.</span>
        </a>

        <nav className="landing-nav-links" aria-label="Sections">
          <a href="#home">Home</a>
          <a href="#platform">Platform</a>
          <a href="#team">Built by</a>
        </nav>

        <div className="landing-nav-actions">
          <div className="connection-pill" title={connected ? "Connected to capture service" : "Capture service offline"}>
            <span className={`pulse-dot ${connected ? "live" : ""}`} />
            <span>{connected ? "Engine ready" : "Local engine"}</span>
          </div>

          <button
            type="button"
            className="landing-cta-btn"
            onClick={onEnterConsole}
            aria-label="Enter console"
          >
            <span>Enter console</span>
            <ArrowUpRight size={16} />
          </button>
        </div>
      </header>

      {/* ─── Hero Section with Video Background ─── */}
      <section id="home" className="landing-hero" aria-label="NetSense network monitoring">
        <div className="hero-video-wrapper">
          <video
            ref={videoRef}
            className="hero-video"
            autoPlay
            muted
            loop
            playsInline
            poster={heroPoster}
            aria-hidden="true"
          >
            <source src={heroVideo} type="video/mp4" />
          </video>
          <div className="hero-overlay" />
        </div>

        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="sparkle" aria-hidden="true">✳</span>
            <span>PACKET-LEVEL NETWORK VISIBILITY</span>
          </div>

          <h1 className="hero-title">
            Understand<br />your network.
          </h1>

          <p className="hero-subtitle">
            A clear view of the traffic flowing through your network.
            <br className="desktop-break" />
            Real packets. Live insights. All in one place.
          </p>

          <div className="hero-actions">
            <button
              type="button"
              className="hero-primary-btn"
              onClick={onEnterConsole}
              id="hero-enter-console-btn"
            >
              <span>Enter console</span>
              <ArrowUpRight size={20} />
            </button>

            <a href="#platform" className="hero-secondary-btn">
              <span>Explore platform</span>
              <ArrowDown size={16} />
            </a>
          </div>
        </div>

        {/* Video Play/Pause Motion Toggle */}
        <button
          type="button"
          className="hero-video-toggle"
          onClick={toggleVideo}
          title={isPlaying ? "Pause background animation" : "Play background animation"}
          aria-label={isPlaying ? "Pause video" : "Play video"}
        >
          {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          <span>{isPlaying ? "Pause video" : "Play video"}</span>
        </button>

        {/* Hero Bottom Fact Bar */}
        <div className="hero-bottom-bar">
          <div className="hero-overline">BUILT FOR A CONNECTED WORLD</div>
          <div className="hero-facts-grid">
            <div className="fact-item">
              <strong>TCP / UDP</strong>
              <small>Protocol visibility</small>
            </div>
            <div className="fact-item">
              <strong>IPv4 / IPv6</strong>
              <small>Dual-stack capture</small>
            </div>
            <div className="fact-item">
              <strong>On your device</strong>
              <small>Local monitoring</small>
            </div>
            <div className="fact-item">
              <strong>100% Private</strong>
              <small>Zero cloud telemetry</small>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Platform Features Section ─── */}
      <section id="platform" className="landing-platform" aria-label="Platform features">
        <div className="section-index">02 / THE PLATFORM</div>
        <div className="platform-container">
          <h2 className="section-heading">
            Visibility starts<br />with real data.
          </h2>
          <p className="section-intro">
            From the first packet to the bigger picture. Know exactly what your network is doing.
          </p>

          <div className="platform-grid">
            <article className="platform-card">
              <div className="platform-icon-wrap">
                <Radio size={24} className="platform-icon" />
              </div>
              <span className="platform-tag">LIVE PACKET CAPTURE</span>
              <h3>Capture at the source.</h3>
              <p>
                Connect directly to your local network adapters and inspect IPv4/IPv6 traffic in real-time
                without sending sensitive data outside your machine.
              </p>
            </article>

            <article className="platform-card">
              <div className="platform-icon-wrap">
                <Activity size={24} className="platform-icon" />
              </div>
              <span className="platform-tag">MEASURED ANALYTICS</span>
              <h3>See the whole session.</h3>
              <p>
                Track live packet rates, bandwidth throughput curves, protocol proportions, and top talkers
                as traffic dynamics shift across seconds.
              </p>
            </article>

            <article className="platform-card">
              <div className="platform-icon-wrap">
                <Network size={24} className="platform-icon" />
              </div>
              <span className="platform-tag">PACKET-LEVEL DETAIL</span>
              <h3>Take a closer look.</h3>
              <p>
                Filter by CIDR subnets, IP endpoints, and port ranges. Drill down into individual bidirectional
                flows or export records into standard CSV files.
              </p>
            </article>
          </div>

          {/* Quick Launch Banner */}
          <div className="platform-banner">
            <div className="banner-text">
              <h4>Ready to inspect your network?</h4>
              <p>Launch the interactive console and start packet capture right away.</p>
            </div>
            <button
              type="button"
              className="banner-cta-btn"
              onClick={onEnterConsole}
            >
              <span>Launch NetSense console</span>
              <ArrowUpRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* ─── Team Section ─── */}
      <section id="team" className="landing-team" aria-label="NetSense creators">
        <div className="section-index">03 / BUILT BY</div>
        <div className="team-container">
          <h2 className="section-heading">Built by engineers.</h2>
          <p className="section-intro">
            The creators behind NetSense's real-time packet telemetry and network intelligence platform.
          </p>

          <div className="team-grid">
            {/* Jose Regish J */}
            <article className="team-card">
              <div className="team-avatar-wrap">
                <img
                  src={joseAvatar}
                  alt="Jose Regish J"
                  className="team-avatar-img"
                />
              </div>
              <h3 className="team-name">Jose Regish J</h3>
              <span className="team-role">Full Stack Developer</span>
              <p className="team-bio">
                Designed the frontend architecture and user interface, and contributed to core backend packet processing.
              </p>
              <a
                href="https://www.linkedin.com/in/hackerjose25/"
                target="_blank"
                rel="noopener noreferrer"
                className="team-linkedin-btn"
                aria-label="Jose Regish J LinkedIn"
              >
                <span>Connect on LinkedIn</span>
                <ExternalLink size={13} />
              </a>
            </article>

            {/* Gayathri M */}
            <article className="team-card">
              <div className="team-avatar-wrap">
                <img
                  src={gayathriAvatar}
                  alt="Gayathri M"
                  className="team-avatar-img"
                />
              </div>
              <h3 className="team-name">Gayathri M</h3>
              <span className="team-role">Backend &amp; ML Developer</span>
              <p className="team-bio">
                Developed, trained, and fine-tuned the machine learning models used for network traffic analysis and packet classification.
              </p>
              <a
                href="https://www.linkedin.com/in/gayathri-m-140279394/"
                target="_blank"
                rel="noopener noreferrer"
                className="team-linkedin-btn"
                aria-label="Gayathri M LinkedIn"
              >
                <span>Connect on LinkedIn</span>
                <ExternalLink size={13} />
              </a>
            </article>

            {/* Dharshini M */}
            <article className="team-card">
              <div className="team-avatar-wrap placeholder">
                <span className="team-avatar-initials">DM</span>
              </div>
              <h3 className="team-name">Dharshini M</h3>
              <span className="team-role">Frontend Developer</span>
              <p className="team-bio">
                Researched the project concept and problem space, and contributed to frontend interface development and styling.
              </p>
              <div className="team-badge">
                <span>Frontend Contributor</span>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="landing-footer">
        <div className="footer-top">
          <a href="#home" className="landing-brand">
            <span className="brand-mark">
              <Activity size={18} strokeWidth={2.5} />
            </span>
            NetSense<span className="brand-dot">.</span>
          </a>
          <span className="footer-slogan">Network visibility. Without the guesswork.</span>
          <a href="#home" className="footer-back-top">Back to top ↑</a>
        </div>
        <div className="footer-bottom">
          <span>&copy; 2026 NetSense Platform</span>
          <span>Engineered by Jose, Gayathri M &amp; Dharshini M</span>
          <span>Real-Time Packet Telemetry</span>
        </div>
      </footer>
    </div>
  );
}

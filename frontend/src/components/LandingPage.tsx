import projectLogo from "../assets/netsense-logo.png";
import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  BrainCircuit,
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
import dharshiniAvatar from "../assets/dharshini.jpeg";

interface LandingPageProps {
  onEnterConsole: () => void;
}

export default function LandingPage({ onEnterConsole }: LandingPageProps) {
  const [isPlaying, setIsPlaying] = useState(() => !window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setIsPlaying(!preference.matches);
    preference.addEventListener("change", change);
    return () => preference.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const sync = () => {
      if (!isPlaying || document.hidden) video.pause();
      else void video.play().catch(() => setIsPlaying(false));
    };
    sync();
    document.addEventListener("visibilitychange", sync);
    return () => document.removeEventListener("visibilitychange", sync);
  }, [isPlaying]);
  const toggleVideo = () => setIsPlaying((playing) => !playing);

  return (
    <div className="landing-container">
      <a className="skip-link" href="#home">Skip to content</a>
      {/* ─── Top Navigation Bar ─── */}
      <header className="landing-nav" aria-label="Landing navigation">
        <a href="#home" className="landing-brand">
          <img className="brand-mark project-logo" src={projectLogo} alt="NetSense logo" />
          NetSense<span className="brand-dot">.</span>
        </a>

        <nav className="landing-nav-links" aria-label="Sections">
          <a href="#home">Home</a>
          <a href="#platform">Platform</a>
          <a href="#workflow">How it works</a>
          <a href="#team">The team</a>
        </nav>

        <div className="landing-nav-actions">
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
      <section id="home" tabIndex={-1} className="landing-hero" aria-label="NetSense network monitoring">
        <div className="hero-video-wrapper">
          <video
            ref={videoRef}
            className="hero-video"
            autoPlay={isPlaying}
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
              <strong>Local-first</strong>
              <small>Capture stays local</small>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Platform Features Section ─── */}
      <section id="platform" className="landing-platform" aria-label="Platform features">
        <div className="platform-container">
          <h2 className="section-heading">
            Visibility starts<br />with real data.
          </h2>
          <p className="section-intro">
            Capture live traffic, investigate connections, and explore model estimates in one focused workspace.
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
            <article className="platform-card">
              <div className="platform-icon-wrap"><BrainCircuit size={24} /></div>
              <span className="platform-tag">MODEL ANALYSIS</span>
              <h3>Find patterns in the packets.</h3>
              <p>Explore packet-size classifications across a capture, compare window results, and download a report with the model's evaluation context.</p>
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
      <section id="workflow" className="landing-workflow" aria-labelledby="workflow-title">
        <div>
          <h2 id="workflow-title" className="section-heading">From traffic to insight.<br />Three simple steps.</h2>
          <p className="section-intro">A practical workflow for a live demo or a closer look at your own network.</p>
          <ol className="workflow-grid">
            <li><span className="step-number">01</span><h3>Choose &amp; capture</h3><p>Open the console, choose a network adapter, and start collecting real packets.</p></li>
            <li><span className="step-number">02</span><h3>Follow the activity</h3><p>Watch traffic rates, filter connections, and identify the endpoints sending the most data.</p></li>
            <li><span className="step-number">03</span><h3>Save &amp; analyze</h3><p>Save a session, run model analysis on at least 10 packets, and export your findings.</p></li>
          </ol>
          <p className="workflow-note"><ShieldCheck size={16} /> Model results describe packet-size patterns. Congestion and threat detection are outside the current model's scope.</p>
        </div>
      </section>

      <section id="team" className="landing-team" aria-label="NetSense creators">
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
              <div className="team-avatar-wrap">
                <img
                  src={dharshiniAvatar}
                  alt="Dharshini M"
                  className="team-avatar-img"
                />
              </div>
              <h3 className="team-name">Dharshini M</h3>
              <span className="team-role">Frontend Developer</span>
              <p className="team-bio">
                Researched the project concept and problem space, and contributed to frontend interface development and styling.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="site-footer">
        <a href="#home" className="landing-brand">
          <img className="brand-mark project-logo" src={projectLogo} alt="NetSense logo" />
          NetSense<span className="brand-dot">.</span>
        </a>
        <span>&copy; {new Date().getFullYear()} NetSense</span>
        <a href="#home" className="footer-back-top">Back to top <ArrowUpRight size={14} /></a>
      </footer>
    </div>
  );
}

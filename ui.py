"""NetSense's visual shell; all telemetry is rendered by live_dashboard."""

from pathlib import Path
import base64

import streamlit as st

ROOT = Path(__file__).resolve().parent


@st.cache_data
def poster_url():
    return "data:image/jpeg;base64," + base64.b64encode((ROOT / "static" / "hero-poster.jpg").read_bytes()).decode("ascii")


def render_shell():
    st.html(f"<style>{(ROOT / 'static' / 'netsense.css').read_text(encoding='utf-8')}</style>")
    st.html('''
    <header class="ns-nav" aria-label="Main navigation">
      <a class="ns-brand" href="#home" aria-label="NetSense home">
        <span class="ns-symbol" aria-hidden="true"><i></i><i></i><i></i></span>NetSense<span class="brand-period">.</span>
      </a>
      <nav class="ns-nav-links" aria-label="Sections">
        <a href="#monitoring">Live monitoring</a>
        <a href="#about">Platform</a>
        <a href="#team">Built by</a>
      </nav>
      <a class="ns-nav-cta" href="#monitoring">Open console <span aria-hidden="true">↗</span></a>
    </header>
    ''')
    with st.container(key="hero"):
        paused = st.session_state.get("pause_hero", False)
        if not paused:
            # Register local media with Streamlit so it is served as video/mp4,
            # supports range requests, and remains referenced by this session.
            # The native element supplies playsinline and muted at construction,
            # which is required for reliable background autoplay on mobile.
            from streamlit.runtime import exists, get_instance
            video_url = get_instance().media_file_mgr.add(
                str(ROOT / "static" / "hero-network.mp4"), "video/mp4", "netsense-hero",
            ) if exists() else ""
            st.html(f'<video class="ns-background-video" autoplay muted loop playsinline preload="auto" poster="{poster_url()}" aria-hidden="true"><source src="{video_url}" type="video/mp4"></video>')
        else:
            st.image(str(ROOT / "static" / "hero-poster.jpg"), width="stretch")
        st.html('''
        <section id="home" class="ns-hero" aria-label="NetSense network monitoring">
          <div class="ns-hero-content">
            <div class="ns-eyebrow"><span class="ns-spark" aria-hidden="true">✳</span> PACKET-LEVEL NETWORK VISIBILITY</div>
            <h1>Understand<br>your network.</h1>
            <p>A clear view of the traffic flowing through your network.<br class="desktop-break"> Real packets. Live insights. All in one place.</p>
            <a class="ns-hero-cta" href="#monitoring">Explore live traffic <span aria-hidden="true">↗</span></a>
          </div>
          <div class="ns-hero-bottom">
            <span class="ns-overline">BUILT FOR A CONNECTED WORLD</span>
            <div class="ns-hero-facts"><span>TCP / UDP <small>Protocol visibility</small></span><span>IPv4 / IPv6 <small>Dual-stack capture</small></span><span>On your device <small>Local monitoring</small></span></div>
          </div>
          <a href="#monitoring" class="ns-scroll" aria-label="Scroll to live monitoring">↓</a>
        </section>
        ''')
        with st.container(key="motion"):
            st.toggle("Pause background video", key="pause_hero")


def get_avatar_html(name_key, initials):
    for ext in ['jpg', 'jpeg', 'png', 'webp']:
        p = ROOT / "images" / f"{name_key}.{ext}"
        if p.exists():
            mime = "image/png" if ext == "png" else "image/jpeg"
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return f'<div class="ns-team-avatar-wrap"><img class="ns-team-avatar-img" src="data:{mime};base64,{b64}" alt="{name_key}"></div>'
    extra_class = " placeholder-avatar" if name_key == "dharshini" else ""
    return f'<div class="ns-team-avatar-wrap{extra_class}"><div class="ns-team-avatar-placeholder">{initials}</div></div>'


def render_footer():
    avatar_jose = get_avatar_html('jose', 'JR')
    avatar_gayathri = get_avatar_html('gayathri', 'GM')
    avatar_dharshini = get_avatar_html('dharshini', 'DM')

    st.html(f'''
    <section class="ns-about" id="about">
      <div class="ns-section-index">02 / THE PLATFORM</div>
      <div class="ns-about-content">
        <h2>Visibility starts<br>with real data.</h2>
        <p class="ns-about-intro">From the first packet to the bigger picture.<br>Know exactly what your network is doing.</p>
        <div class="ns-feature-grid">
          <article><span class="ns-feature-icon">↗</span><h3>Capture at the source.</h3><p>Connect to your network adapter and observe IPv4 and IPv6 traffic directly on your device.</p><span class="ns-tag">LIVE PACKET CAPTURE</span></article>
          <article><span class="ns-feature-icon">≋</span><h3>See the whole session.</h3><p>Track packet rates, captured throughput, and protocol distribution as your traffic changes.</p><span class="ns-tag">MEASURED ANALYTICS</span></article>
          <article><span class="ns-feature-icon">↓</span><h3>Take a closer look.</h3><p>Inspect packet timestamps, endpoints, and sizes. Export your recent observations for further analysis.</p><span class="ns-tag">PACKET-LEVEL DETAIL</span></article>
        </div>
      </div>
    </section>

    <section class="ns-team" id="team">
      <div class="ns-section-index">03 / BUILT BY</div>
      <div class="ns-team-content">
        <h2>Built by engineers.</h2>
        <p class="ns-team-intro">The creators behind NetSense's real-time packet telemetry and network intelligence platform.</p>
        <div class="ns-team-grid">
          
          <!-- Builder 1: Jose Regish J -->
          <article class="ns-team-card">
            {avatar_jose}
            <h3 class="ns-team-name">Jose Regish J</h3>
            <span class="ns-team-role">Full Stack Developer</span>
            <p class="ns-team-bio">Designed the frontend interface and experience, and helped build core parts of the backend and telemetry architecture.</p>
            <a class="ns-linkedin-btn" href="https://www.linkedin.com/in/hackerjose25/" target="_blank" rel="noopener noreferrer" aria-label="Jose Regish J LinkedIn Profile">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              <span>Connect on LinkedIn</span>
            </a>
          </article>

          <!-- Builder 2: Gayathri M -->
          <article class="ns-team-card">
            {avatar_gayathri}
            <h3 class="ns-team-name">Gayathri M</h3>
            <span class="ns-team-role">Backend &amp; ML Developer</span>
            <p class="ns-team-bio">Developed and trained the machine learning models used for network traffic analysis and packet classification.</p>
            <a class="ns-linkedin-btn" href="https://www.linkedin.com/in/gayathri-m-140279394/" target="_blank" rel="noopener noreferrer" aria-label="Gayathri M LinkedIn Profile">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              <span>Connect on LinkedIn</span>
            </a>
          </article>

          <!-- Builder 3: Dharshini M -->
          <article class="ns-team-card ns-team-card-pending">
            <!-- Dedicated slot for Dharshini M profile photo -->
            {avatar_dharshini}
            <h3 class="ns-team-name">Dharshini M</h3>
            <span class="ns-team-role">Frontend Developer</span>
            <p class="ns-team-bio">Researched the project concept and problem space, and contributed to frontend interface development and styling.</p>
            <div class="ns-linkedin-btn pending" title="Profile Details Coming Soon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
              <span>Profile Space Ready</span>
            </div>
          </article>

        </div>
      </div>
    </section>

    <footer class="ns-footer">
      <div class="ns-footer-top">
        <a class="ns-brand" href="#home">NetSense<span class="brand-period">.</span></a>
        <span>Network visibility. Without the guesswork.</span>
        <a href="#home">Back to top ↑</a>
      </div>
      <div class="ns-footer-bottom">
        <span>&copy; 2026 NetSense Platform</span>
        <span>Engineered by Jose, Gayathri M &amp; Dharshini M</span>
        <span>Real-Time Packet Telemetry</span>
      </div>
    </footer>
    ''')

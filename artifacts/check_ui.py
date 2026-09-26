"""Manual browser smoke check; requires Playwright and installed Edge."""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8502"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL)
    page.locator(".ns-background-video").wait_for(state="attached", timeout=30000)
    page.wait_for_function('document.querySelector("video").currentTime > 0', timeout=20000)
    print("VIDEO", page.locator("video").evaluate("v => ({time:v.currentTime,muted:v.muted,loop:v.loop,inline:v.playsInline})"), flush=True)
    page.screenshot(path="artifacts/netsense-desktop.png")
    page.get_by_role("link", name="Open console").click()
    try:
        page.get_by_role("button", name="Start Live Capture", exact=True).click()
        page.wait_for_function('document.querySelectorAll(".ns-metric-value")[2]?.getAttribute("aria-label")?.startsWith("Packet rate: ") && document.querySelectorAll(".ns-metric-value")[2]?.getAttribute("aria-label") !== "Packet rate: Unavailable"', timeout=60000)
        assert page.locator('[data-testid="stException"]').count() == 0
        print("LIVE STATUS", page.locator(".ns-status-main").inner_text(), flush=True)
        print("LIVE METRICS", page.locator(".ns-metric-value").all_text_contents(), flush=True)
        page.screenshot(path="artifacts/netsense-console-live.png")
        page.get_by_role("tab", name="Packet explorer").click()
        page.wait_for_timeout(1000)
        print("TABLES", page.locator('[data-testid="stDataFrame"]').count(), flush=True)
        print("TABS", page.get_by_role("tab").evaluate_all('es => es.map(e=>[e.textContent,e.getAttribute("aria-selected")])'), flush=True)
        page.screenshot(path="artifacts/netsense-packets.png")
        assert page.locator('[data-testid="stDataFrame"]').count() == 1
    finally:
        stop = page.get_by_role("button", name="Stop Capture", exact=True)
        if stop.is_enabled():
            stop.click()
        page.wait_for_timeout(1500)
        print("STOP", page.locator(".ns-status-main").inner_text(), flush=True)
        print("STOP METRICS", page.locator(".ns-metric-value").all_text_contents(), flush=True)

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=1)
    mobile.goto(URL)
    mobile.locator(".ns-hero").wait_for(state="visible", timeout=30000)
    mobile.screenshot(path="artifacts/netsense-mobile.png")
    assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth")
    mobile.get_by_text("Pause background video", exact=True).click()
    mobile.locator(".ns-background-video").wait_for(state="detached", timeout=15000)
    print("MOBILE video pause passed", flush=True)
    mobile.get_by_role("link", name="Open console").click()
    mobile.screenshot(path="artifacts/netsense-mobile-console.png")
    assert mobile.locator('[data-testid="stException"]').count() == 0
    print("MOBILE layout passed", flush=True)
    browser.close()

"""Screenshot the QuoteRadar dashboard for both currencies.

Produces desktop (light + dark) and mobile (light) stills. The mobile shot is the
one that matters for outreach - prospects open WhatsApp on a phone.

Usage:  python capture_ui.py
"""
import os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))

EDITIONS = {
    "uae":      "quoteradar_dashboard_aed.html",
    "pakistan": "quoteradar_dashboard_pkr.html",
}

SHOTS = [
    # name,        width, height, scheme, scale
    ("desktop_light", 1500, 1000, "light", 2),
    ("desktop_dark",  1500, 1000, "dark",  2),
    ("mobile_light",   430,  932, "light", 3),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for edition, src in EDITIONS.items():
            path = os.path.join(HERE, src)
            url = "file:///" + path.replace("\\", "/")

            for name, w, h, scheme, scale in SHOTS:
                page = browser.new_page(
                    viewport={"width": w, "height": h},
                    device_scale_factor=scale,
                    color_scheme=scheme,
                )
                page.goto(url)
                # let the count-up animation settle on its final value
                page.wait_for_timeout(1500)

                out = os.path.join(HERE, "ui_%s_%s.png" % (edition, name))
                page.screenshot(path=out, full_page=True)
                page.close()

                print("%-9s %-14s %dx%d @%dx -> %.2f MB" % (
                    edition, name, w, h, scale, os.path.getsize(out) / 1e6))

        browser.close()


if __name__ == "__main__":
    main()

"""Frame-exact capture of the QuoteRadar product film.

Why frame-stepping instead of Playwright's built-in video recorder: the recorder
samples in real time, so any stutter on the host drops frames. Here the page's
clock is decoupled from wall time — window.__seek(ms) scrubs every CSS animation
to an exact currentTime — so each frame is rendered deterministically and the
output is identical no matter how slow the machine is.

Usage:
    python capture_film.py                 # both editions
    python capture_film.py uae             # one edition
"""
import os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
W, H = 1920, 1080

EDITIONS = {
    "uae":      ("quoteradar_film_aed.html", "quoteradar_film_uae.mp4"),
    "pakistan": ("quoteradar_film_pkr.html", "quoteradar_film_pakistan.mp4"),
}


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    root = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    for base, _dirs, files in os.walk(root):
        if "ffmpeg.exe" in files:
            return os.path.join(base, "ffmpeg.exe")
    raise SystemExit("ffmpeg not found - install it first (winget install Gyan.FFmpeg)")


def capture(src_html, out_mp4, ffmpeg, lossless=False):
    """lossless=True captures PNG frames (pixel-exact) and encodes at CRF 12.
    Slower and much larger; worth it only for YouTube or file-transfer delivery,
    since WhatsApp re-encodes video regardless of what you feed it."""
    from playwright.sync_api import sync_playwright

    src = os.path.join(HERE, src_html)
    # Per-edition frame dir, so a resumed run cannot mix two films together.
    frames_dir = os.path.join(HERE, "_frames_" + os.path.splitext(out_mp4)[0])
    os.makedirs(frames_dir, exist_ok=True)

    url = "file:///" + src.replace("\\", "/") + "?render=1"
    t_start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--force-device-scale-factor=1",
            "--disable-dev-shm-usage",   # small /dev/shm stalls screenshots on low-RAM hosts
            "--disable-gpu",
        ])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_default_timeout(120000)
        page.goto(url)
        page.wait_for_function("typeof window.__seek === 'function'")

        total = page.evaluate("window.__total")
        count = int(round(total / 1000.0 * FPS))
        print("  %s -> %d frames @ %dfps (%.1fs)" % (src_html, count, FPS, total / 1000.0))

        ext = "png" if lossless else "jpg"
        for i in range(count):
            dest = os.path.join(frames_dir, "f%05d.%s" % (i, ext))
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                continue                      # resume: keep frames from a prior attempt

            shot = {"path": dest}
            if not lossless:
                shot.update(type="jpeg", quality=95)

            # A screenshot can stall on a loaded host; retry rather than lose the run.
            for attempt in range(4):
                try:
                    page.evaluate("ms => window.__seek(ms)", i * 1000.0 / FPS)
                    page.screenshot(**shot)
                    break
                except Exception as err:
                    if attempt == 3:
                        raise
                    print("    frame %d retry %d (%s)" % (i, attempt + 1, type(err).__name__))
                    page.wait_for_timeout(1500)

            if i and i % 300 == 0:
                print("    %d/%d" % (i, count))

        browser.close()

    print("  encoding...")
    out = os.path.join(HERE, out_mp4)
    subprocess.run([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "f%05d." + ext),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "12" if lossless else "18",
        "-pix_fmt", "yuv420p",        # required for WhatsApp / QuickTime
        "-movflags", "+faststart",    # starts playing before fully downloaded
        out,
    ], check=True)

    shutil.rmtree(frames_dir, ignore_errors=True)
    size = os.path.getsize(out) / 1e6
    print("  done: %s  (%.1f MB, %.0fs)" % (out_mp4, size, time.time() - t_start))


if __name__ == "__main__":
    args = sys.argv[1:]
    lossless = "--lossless" in args
    wanted = [a for a in args if not a.startswith("--")] or list(EDITIONS)

    ffmpeg = find_ffmpeg()
    print("ffmpeg:", ffmpeg, "| lossless:", lossless)
    for name in wanted:
        print(name + ":")
        capture(*EDITIONS[name], ffmpeg=ffmpeg, lossless=lossless)

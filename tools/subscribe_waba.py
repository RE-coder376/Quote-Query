"""Subscribe this app to a WhatsApp Business Account's webhook events.

There are two subscriptions and both are required:
  1. app -> whatsapp_business_account object  (done via app token; see setup notes)
  2. WABA -> this app                          (this script; needs a USER token)

Step 2 needs `whatsapp_business_management`, which an app access token does not
carry. The temporary token on the API Setup page does.

    python -m tools.subscribe_waba <WABA_ID> <TEMP_ACCESS_TOKEN>

The token is passed as an argument so it never has to be written down anywhere.
It expires in ~24h, which is fine - this is a one-time wiring step.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def call(method: str, path: str, token: str, params: dict | None = None):
    p = dict(params or {})
    p["access_token"] = token
    if method == "POST":
        req = urllib.request.Request(f"{GRAPH}/{path}",
                                     data=urllib.parse.urlencode(p).encode(),
                                     method="POST")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}?" + urllib.parse.urlencode(p))
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)

    waba, token = sys.argv[1], sys.argv[2]

    status, body = call("POST", f"{waba}/subscribed_apps", token)
    if status == 200 and body.get("success"):
        print("OK  app subscribed to WABA", waba)
    else:
        print("FAILED", status, body.get("error", {}).get("message", body))
        print("\nIf it says the token is invalid or expired, copy a fresh one from")
        print("the API Setup page and run this again.")
        raise SystemExit(1)

    status, body = call("GET", f"{waba}/subscribed_apps", token)
    print("current subscribers ->", status, json.dumps(body)[:300])


if __name__ == "__main__":
    main()

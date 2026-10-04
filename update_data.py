import datetime
import json
import os
import sys

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
DATA_FILE = "data.json"


def load_current():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def clean_items(items, with_confirmed):
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title", "")).strip()
        details = str(it.get("details", "")).strip()
        source = str(it.get("source", "")).strip()
        if not title or not details:
            continue
        if source and not source.startswith("http"):
            source = ""
        item = {"title": title[:160], "details": details[:1500], "source": source}
        if with_confirmed:
            cat = str(it.get("category", "")).strip().lower()
            item["category"] = cat if cat in ("packs", "royale_pass", "events") else "packs"
            item["confirmed"] = bool(it.get("confirmed", False))
        out.append(item)
    return out


def main():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("No ANTHROPIC_API_KEY secret set. Skipping update.")
        return 0

    today = datetime.date.today().isoformat()
    prompt = (
        "Today is %s. Research the latest information about the global PUBG Mobile game using web search: "
        "(1) the current and next game version and its new features, modes, maps and special abilities, "
        "(2) the current and next season and Royale Pass, "
        "(3) upcoming leaked or announced crates, premium crates, lucky spins, ultimate sets and upgradable weapon skins (category packs), "
        "(4) the full leaked rewards of the next Royale Pass tier by tier when available (category royale_pass), "
        "(5) upcoming in-game events with dates (category events). "
        "Write everything in clear Arabic, in your own words. Never invent facts and never include redeem codes or sensitivity codes. "
        "Set confirmed to true only when the information comes from the official PUBG Mobile website or official channels, otherwise false. "
        "Each item must have a source URL taken from your search results. "
        "Reply with JSON only, no other text, in exactly this shape: "
        '{"upcoming":[{"title":"...","details":"...","source":"https://..."}],'
        '"leaks":[{"title":"...","category":"packs","details":"...","confirmed":false,"source":"https://..."}]} '
        "category must be one of packs, royale_pass, events. Use at most 8 upcoming items and 14 leaks items."
    ) % today

    try:
        resp = requests.post(
            API_URL,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 6000,
                "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=240,
        )
        if resp.status_code != 200:
            print("API error:", resp.status_code, resp.text[:300])
            return 0
        blocks = resp.json().get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            print("No JSON in reply. Keeping the current data.")
            return 0
        parsed = json.loads(text[start : end + 1])
    except Exception as exc:
        print("Update failed, keeping the current data:", exc)
        return 0

    upcoming = clean_items(parsed.get("upcoming"), False)
    leaks = clean_items(parsed.get("leaks"), True)
    if len(upcoming) + len(leaks) < 3:
        print("Too little data returned. Keeping the current data.")
        return 0

    data = load_current()
    data["version"] = int(data.get("version", 0)) + 1
    data["updated"] = today
    data["upcoming"] = upcoming
    data["leaks"] = leaks
    data.setdefault("sensitivity_codes", [])
    data.setdefault("redeem_codes", [])
    data.setdefault("links", [])
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json updated:", len(upcoming), "upcoming,", len(leaks), "leaks")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
GitHub Contributions Adapter
GitHub GraphQL → normalized weeks[].days[] → V2 culture_model

Supports:
  DATA_SOURCE=sample  → local sample-contributions.json fixture
  DATA_SOURCE=github  → live GraphQL (needs GITHUB_TOKEN + GITHUB_USERNAME)

Normalized schema (preserved from data.py):
  { "weeks": [{ "days": [{ "date": str, "weekday": int 0-6, "count": int, "level": int 0-4 }] *7 }] *53 }

The renderer (culture_model) never calls the API itself.
"""
import os
import json
import datetime

N_WEEKS = 53
N_DAYS = 7

def level_for_count(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4

def load_sample(path: str = None) -> dict:
    if path is None:
        # try neural/culture-v2 then neural/v1 then root
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "neural", "culture-v2", "sample-contributions.json"),
            os.path.join(os.path.dirname(__file__), "..", "neural", "v1", "sample-contributions.json"),
            os.path.join(os.path.dirname(__file__), "..", "Other claude generated", "neural-culture-v2", "sample-contributions.json"),
            "neural/culture-v2/sample-contributions.json",
            "sample-contributions.json",
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break
    if not path or not os.path.exists(path):
        raise FileNotFoundError("sample-contributions.json not found")
    with open(path, "r") as f:
        return json.load(f)

def fetch_github(username: str, token: str) -> dict:
    import urllib.request
    import urllib.error

    query = """
    query($user:String!) {
      user(login:$user) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays { date weekday contributionCount contributionLevel }
            }
          }
        }
      }
    }
    """
    # GitHub levels map: NONE/FIRST/ SECOND/ THIRD/ FOURTH → 0-4
    level_map = {"NONE":0, "FIRST_QUARTILE":1, "SECOND_QUARTILE":2, "THIRD_QUARTILE":3, "FOURTH_QUARTILE":4}
    payload = json.dumps({"query": query, "variables": {"user": username}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "neural-culture-adapter",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code}: {e.read().decode()[:500]}")
    if "errors" in body:
        raise RuntimeError(f"GraphQL errors: {body['errors']}")
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    # Normalize: ensure 53 weeks, map fields
    normalized = {"weeks": []}
    for wk in weeks[-N_WEEKS:]:
        days = []
        for d in wk["contributionDays"]:
            # weekday: GitHub returns 0=Sun, matches our 0=Sun
            days.append({
                "date": d["date"],
                "weekday": d.get("weekday", 0),
                "count": d["contributionCount"],
                "level": level_map.get(d["contributionLevel"], level_for_count(d["contributionCount"])),
            })
        # pad/truncate to 7
        while len(days) < 7:
            # infer date
            last = datetime.date.fromisoformat(days[-1]["date"]) if days else datetime.date.today()
            nxt = last + datetime.timedelta(days=1)
            days.append({"date": nxt.isoformat(), "weekday": (days[-1]["weekday"]+1)%7 if days else 0, "count":0, "level":0})
        normalized["weeks"].append({"days": days[:7]})
    # pad weeks if <53 (new account)
    while len(normalized["weeks"]) < N_WEEKS:
        normalized["weeks"].insert(0, {"days": [
            {"date": (datetime.date.today()-datetime.timedelta(days=(N_WEEKS-len(normalized["weeks"]))*7+i)).isoformat(), "weekday":i%7, "count":0, "level":0} for i in range(7)
        ]})
    return normalized

def fetch_via_jogruber(username: str) -> dict:
    import urllib.request, json, datetime, ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    all_days = []
    for y in [2024, 2025, 2026]:
        url = f"https://github-contributions-api.jogruber.de/v4/{username}?y={y}"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode())
                for c in data.get("contributions", []):
                    all_days.append({"date": c["date"], "count": c["count"], "level": c["level"]})
        except Exception as e:
            print(f"jogruber {y} failed: {e}")
    if not all_days:
        raise RuntimeError("jogruber returned no data")
    # sort by date, keep only past+today, then take last 371
    all_days.sort(key=lambda x: x["date"])
    today = datetime.date.today()
    # keep only dates <= today (ignore future zeros from API)
    past = [d for d in all_days if datetime.date.fromisoformat(d["date"]) <= today]
    if past:
        all_days = past
    # take last N_WEEKS*7 days (371)
    tail = all_days[-N_WEEKS*7:]
    # ensure exactly 371, pad leading zeros if needed
    while len(tail) < N_WEEKS*7:
        first = datetime.date.fromisoformat(tail[0]["date"]) - datetime.timedelta(days=1)
        tail.insert(0, {"date": first.isoformat(), "count": 0, "level": 0})
    # build weeks
    weeks = []
    # align start to Sunday
    start_date = datetime.date.fromisoformat(tail[0]["date"])
    # weekday from date: Monday=0 in python, need Sun=0
    # compute weekday for each
    for w in range(N_WEEKS):
        days = []
        for d in range(7):
            idx = w*7 + d
            entry = tail[idx]
            dt = datetime.date.fromisoformat(entry["date"])
            # python weekday Monday0 -> Sunday6, convert to Sunday0
            wd = (dt.weekday() + 1) % 7
            days.append({"date": entry["date"], "weekday": wd, "count": entry["count"], "level": entry["level"]})
        weeks.append({"days": days})
    return {"weeks": weeks}

def load_contributions(source: str = None, username: str = None, token: str = None) -> dict:
    source = (source or os.environ.get("DATA_SOURCE") or "sample").lower()
    if source == "github":
        username = username or os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or os.environ.get("USER")
        if not username and os.environ.get("GITHUB_REPOSITORY"):
            username = os.environ["GITHUB_REPOSITORY"].split("/")[0]
        token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not username:
            # default to ArjunPakhan as spec says confirmed
            username = "ArjunPakhan"
        if token:
            try:
                return fetch_github(username, token)
            except Exception as e:
                print(f"GraphQL failed ({e}), falling back to jogruber for {username}")
        # fallback public API (no token needed)
        return fetch_via_jogruber(username)
    # default sample
    return load_sample()

def validate(data: dict) -> bool:
    assert "weeks" in data, "missing weeks"
    assert len(data["weeks"]) == 53, f"expected 53 weeks got {len(data['weeks'])}"
    for w in data["weeks"]:
        assert "days" in w and len(w["days"]) == 7, "each week needs 7 days"
        for d in w["days"]:
            for k in ("date","weekday","count","level"):
                assert k in d, f"missing {k}"
            assert 0 <= d["weekday"] <= 6
            assert 0 <= d["level"] <= 4
    return True

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=["sample","github"], default=os.environ.get("DATA_SOURCE","sample"))
    p.add_argument("--username")
    p.add_argument("--out", default="neural/culture-v2/sample-contributions.json")
    args = p.parse_args()
    data = load_contributions(source=args.source, username=args.username)
    validate(data)
    print(f"loaded {args.source} {len(data['weeks'])} weeks, {sum(1 for w in data['weeks'] for d in w['days'] if d['count']>0)} active days")
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"wrote {args.out}")

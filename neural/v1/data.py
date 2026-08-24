"""
Sample contribution-graph dataset generator.

Shape deliberately mirrors GitHub's GraphQL `contributionsCollection.contributionCalendar`:

    {
      "weeks": [
        {
          "days": [
            {"date": "2025-08-24", "weekday": 0, "count": 3, "level": 2},
            ...
          ]
        },
        ...
      ]
    }

weekday: 0=Sun .. 6=Sat (matches GitHub's top-to-bottom row order)
level:   0-4 (matches GitHub's contribution intensity buckets)

Swapping this for real data later = write an adapter that produces this same
`weeks[].days[]` shape from the GitHub API response. The renderer never needs
to change.
"""
import json
import random
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


def generate(seed: int = 42) -> dict:
    rng = random.Random(seed)

    today = datetime.date(2026, 8, 22)  # a Saturday, so the grid ends cleanly
    start = today - datetime.timedelta(days=N_WEEKS * 7 - 1)
    # roll back to the preceding Sunday so weekday 0 always starts a column
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    # smooth random walk driving "how active is this week generally"
    week_level = 0.15  # starts sparse (early period), ramps up like a real history
    week_levels = []
    for w in range(N_WEEKS):
        drift = rng.uniform(-0.16, 0.20)
        # gentle upward bias over the year, gentle mean reversion
        week_level += drift + (0.012 if w < 30 else -0.004)
        week_level = max(0.0, min(1.35, week_level))
        week_levels.append(week_level)

    # scripted bursts: a couple of "hackathon-ish" dense weeks for cluster-burst testing
    for burst_week in (14, 15, 33, 47):
        if burst_week < N_WEEKS:
            week_levels[burst_week] = max(week_levels[burst_week], 1.15)

    # a couple of scripted dead weeks (travel / break) to test fast-through-gaps motion
    for dead_week in (5, 22, 40):
        if dead_week < N_WEEKS:
            week_levels[dead_week] = 0.02

    weeks = []
    d = start
    for w in range(N_WEEKS):
        wl = week_levels[w]
        days = []
        for wd in range(N_DAYS):
            weekend_damp = 0.55 if wd in (0, 6) else 1.0
            p_active = min(0.94, wl * 0.62 * weekend_damp)
            active = rng.random() < p_active
            if active:
                intensity_roll = rng.random() * wl
                if intensity_roll > 0.95:
                    count = rng.randint(10, 16)
                elif intensity_roll > 0.65:
                    count = rng.randint(6, 9)
                elif intensity_roll > 0.32:
                    count = rng.randint(3, 5)
                else:
                    count = rng.randint(1, 2)
            else:
                count = 0
            days.append({
                "date": d.isoformat(),
                "weekday": wd,
                "count": count,
                "level": level_for_count(count),
            })
            d += datetime.timedelta(days=1)
        weeks.append({"days": days})

    return {"weeks": weeks}


if __name__ == "__main__":
    data = generate()
    with open("sample-contributions.json", "w") as f:
        json.dump(data, f, indent=2)
    total = sum(1 for w in data["weeks"] for day in w["days"] if day["count"] > 0)
    print(f"generated {total} active days across {N_WEEKS} weeks")

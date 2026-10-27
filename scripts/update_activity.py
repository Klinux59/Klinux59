"""Generate a self-hosted card from PUBLIC GitHub API endpoints only.
The event chart covers the last 30 UTC calendar dates, capped at 300 returned
events by the API. Events are not commits or GitHub contribution counts.
Docs: https://docs.github.com/en/rest/activity/events
"""
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request


def api(path):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "Thanaphat59-profile",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com/" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def text(x, y, value, size=14, color="#a6b8d3", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{html.escape(str(value))}</text>'


def render(user, events, today):
    dates = [today - dt.timedelta(days=29-i) for i in range(30)]
    counts = collections.Counter(
        event["created_at"][:10] for event in events if event.get("public") is True
    )
    values = [counts[date.isoformat()] for date in dates]
    peak = max(values) or 1
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="365" viewBox="0 0 1200 365" role="img" aria-labelledby="title desc">',
             '<title id="title">Klinux59 public GitHub activity</title>',
             '<desc id="desc">Public repository and follower counts, plus daily public events over the last 30 UTC calendar dates. Events are capped at the latest 300 and are not commit or contribution counts.</desc>',
             '<rect x="1" y="1" width="1198" height="363" rx="18" fill="#0c1424" stroke="#26344b"/>',
             '<g font-family="Segoe UI,Arial,sans-serif">',
             text(34, 38, "PUBLIC GITHUB ACTIVITY", 12, "#73e4ee", 'letter-spacing="2"'),
             text(1166, 38, "@Klinux59", 12, "#7f93b1", 'text-anchor="end"')]
    metrics = [(user["public_repos"], "PUBLIC REPOS"), (user["followers"], "FOLLOWERS"),
               (user["following"], "FOLLOWING"), (sum(values), "PUBLIC EVENTS / 30 DAYS")]
    for i, (value, label) in enumerate(metrics):
        x = 34 + i * 291
        parts += [text(x, 101, value, 36, "#e4ecfb", 'font-weight="600"'),
                  text(x, 127, label, 10, "#8b9db9", 'letter-spacing="1.3"')]
    parts += ['<path d="M34 151H1166" stroke="#26344b"/>',
              text(34, 181, "RECENT PUBLIC EVENTS", 11, "#a0b5d3", 'letter-spacing="1.5"')]
    for i, value in enumerate(values):
        x = 42 + i * 37.5
        height = max(3, value / peak * 90)
        color = "#69dce9" if value else "#20334e"
        label = html.escape(f"{dates[i]}: {value} public events")
        parts.append(f'<rect x="{x}" y="{292-height}" width="22" height="{height}" rx="3" fill="{color}"><title>{label}</title></rect>')
        if i in (0, 7, 14, 21, 29):
            parts.append(text(x+11, 313, dates[i].strftime("%d %b"), 10, "#8296b4", 'text-anchor="middle"'))
    if not sum(values):
        parts.append(text(600, 236, "No public events returned for this period.", 14, "#8ca1c0", 'text-anchor="middle"'))
    parts += [text(34, 345, f"PUBLIC DATA ONLY · UTC · UPDATED {today}", 10, "#7286a5"),
              text(1166, 345, "LATEST 300 EVENTS · EVENTS ARE NOT COMMITS", 10, "#7286a5", 'text-anchor="end"'),
              '</g></svg>\n']
    return "\n".join(parts)


def main():
    user = api("users/Klinux59")
    events = []
    for page in range(1, 4):
        batch = api(f"users/Klinux59/events/public?per_page=100&page={page}")
        events.extend(batch)
        if len(batch) < 100:
            break
    today = dt.datetime.now(dt.timezone.utc).date()
    output = Path(__file__).resolve().parents[1] / "assets" / "activity.svg"
    output.write_text(render(user, events, today), encoding="utf-8")


if __name__ == "__main__":
    main()


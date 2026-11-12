"""Collect site visits from ntfy and send a weekly summary.

collect: read the last 12 h of the visits topic and add new ones to data/visits.jsonl
summary: count the last 7 days by country and push one message to the summary topic
"""
import json, os, re, sys, time, urllib.request
from collections import Counter

VISITS = "https://ntfy.sh/pocus27-visits-d2ea349b"
SUMMARY = "https://ntfy.sh/pocus27-weekly-d2ea349b"
REG = "https://ntfy.sh/pocus27-reg-360b059e6c"
LOG = "data/visits.jsonl"
REGLOG = "data/reg-clicks.jsonl"
ZI = "/usr/share/zoneinfo/"

def fetch(url):
    # ntfy.sh is sometimes briefly unreachable from the runner; retry before failing
    for i in range(3):
        try:
            return urllib.request.urlopen(url, timeout=30).read().decode()
        except OSError:
            if i == 2:
                raise
            time.sleep(30)

def countries():
    names = {}
    for line in open(ZI + "iso3166.tab", encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            code, name = line.rstrip("\n").split("\t")[:2]
            names[code] = name
    tz = {}
    for line in open(ZI + "zone.tab", encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            p = line.split("\t")
            tz[p[2].strip()] = names.get(p[0], p[0])
    return tz

def load(path=LOG):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

def collect_reg():
    seen = {v["id"] for v in load(REGLOG)}
    raw = fetch(REG + "/json?poll=1&since=12h")
    new = []
    for line in raw.splitlines():
        m = json.loads(line)
        if m.get("event") != "message" or m["id"] in seen:
            continue
        t = re.search(r"Registration click: (.+?) · from (.+)", m.get("message", ""))
        if t:
            new.append({"id": m["id"], "time": m["time"], "type": t.group(1).strip(), "tz": t.group(2).strip()})
    with open(REGLOG, "a", encoding="utf-8") as f:
        for v in new:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    print(len(new), "new registration clicks")

def collect():
    seen = {v["id"] for v in load()}
    raw = fetch(VISITS + "/json?poll=1&since=12h")
    new = []
    for line in raw.splitlines():
        m = json.loads(line)
        if m.get("event") != "message" or m["id"] in seen:
            continue
        t = re.search(r"Visitor from (.+?) · language (.+?) · first page: (\S+)", m.get("message", ""))
        if t:
            new.append({"id": m["id"], "time": m["time"], "tz": t.group(1), "lang": t.group(2), "page": t.group(3)})
    with open(LOG, "a", encoding="utf-8") as f:
        for v in new:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    print(len(new), "new visits")
    collect_reg()

def local(v):
    """Visit time in the visitor's own time zone (falls back to Swedish time)."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    for name in (v["tz"].replace(" ", "_"), "Europe/Stockholm"):
        try:
            return datetime.fromtimestamp(v["time"], timezone.utc).astimezone(ZoneInfo(name))
        except Exception:
            pass

def bar(n, top):
    return "\u2588" * max(1, round(8 * n / top)) if n else ""

def summary(days=7):
    tz = countries()
    since = time.time() - days * 86400
    week = [v for v in load() if v["time"] >= since]
    if not week:
        body = "No visits in the last 7 days."
    else:
        by = Counter(tz.get(v["tz"].replace(" ", "_"), v["tz"]) for v in week)
        times = [local(v) for v in week]
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        wd = Counter(t.weekday() for t in times)
        slots = [("Night 00-06", 0, 6), ("Morning 06-12", 6, 12), ("Afternoon 12-18", 12, 18), ("Evening 18-24", 18, 24)]
        sl = Counter(next(n for n, a, b in slots if a <= t.hour < b) for t in times)
        pages = Counter(v["page"] for v in week)
        lines = [f"{len(week)} visits in the last 7 days", "", "COUNTRY"]
        lines += [f"{c}: {k}" for c, k in by.most_common()]
        lines += ["", "DAY OF THE WEEK"]
        top = max(wd.values())
        lines += [f"{names[d]}: {wd[d]} {bar(wd[d], top)}" for d in range(7)]
        lines += ["", "TIME OF DAY (visitor's local time)"]
        top = max(sl.values())
        lines += [f"{n}: {sl[n]} {bar(sl[n], top)}" for n, a, b in slots]
        lines += ["", "First page: " + ", ".join(f"{p} ({k})" for p, k in pages.most_common(3))]
        body = "\n".join(lines)
    reg = [v for v in load(REGLOG) if v["time"] >= since]
    rl = ["", f"REGISTRATION CLICKS: {len(reg)}"]
    if reg:
        rl += [f"{t}: {k}" for t, k in Counter(v["type"] for v in reg).most_common()]
        rl += ["From: " + ", ".join(f"{c} ({k})" for c, k in Counter(tz.get(v["tz"].replace(" ", "_"), v["tz"]) for v in reg).most_common())]
    body += "\n" + "\n".join(rl)
    print(body)
    req = urllib.request.Request(SUMMARY, data=body.encode(), headers={"Title": "POCUS 2027 website: weekly visitors"})
    urllib.request.urlopen(req, timeout=30)
    open("data/last-summary.txt", "w").write(time.strftime("%Y-%m-%d %H:%M UTC\n", time.gmtime()))

if __name__ == "__main__":
    {"collect": collect, "summary": summary}[sys.argv[1]]()

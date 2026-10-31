"""Collect site visits from ntfy and send a weekly summary.

collect: read the last 12 h of the visits topic and add new ones to data/visits.jsonl
summary: count the last 7 days by country and push one message to the summary topic
"""
import json, os, re, sys, time, urllib.request
from collections import Counter

VISITS = "https://ntfy.sh/pocus27-visits-d2ea349b"
SUMMARY = "https://ntfy.sh/pocus27-weekly-d2ea349b"
LOG = "data/visits.jsonl"
ZI = "/usr/share/zoneinfo/"

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

def load():
    if not os.path.exists(LOG):
        return []
    return [json.loads(l) for l in open(LOG, encoding="utf-8") if l.strip()]

def collect():
    seen = {v["id"] for v in load()}
    raw = urllib.request.urlopen(VISITS + "/json?poll=1&since=12h", timeout=30).read().decode()
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

def summary(days=7):
    tz = countries()
    since = time.time() - days * 86400
    week = [v for v in load() if v["time"] >= since]
    by = Counter(tz.get(v["tz"].replace(" ", "_"), v["tz"]) for v in week)
    pages = Counter(v["page"] for v in week)
    if week:
        lines = [f"{len(week)} visits in the last 7 days", ""] + [f"{c}: {k}" for c, k in by.most_common()]
        lines += ["", "Most visited first page: " + ", ".join(f"{p} ({k})" for p, k in pages.most_common(3))]
    else:
        lines = ["No visits in the last 7 days."]
    body = "\n".join(lines)
    print(body)
    req = urllib.request.Request(SUMMARY, data=body.encode(), headers={"Title": "POCUS 2027 website: weekly visitors"})
    urllib.request.urlopen(req, timeout=30)

if __name__ == "__main__":
    {"collect": collect, "summary": summary}[sys.argv[1]]()

"""Generate inferred (transitive) prerequisite relationships from prerequisites.csv.

Outputs:
- data/inferred_prerequisites.csv  (course_id, prereq_id, distance)
- prints a short report of missing courses referenced in prerequisites.

Usage:
  python scripts/generate_full_prereqs.py

This is a helper for the demo; run locally and inspect the generated CSV before replacing the original.
"""
import csv
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PREREQ_CSV = DATA / 'prerequisites.csv'
COURSES_CSV = DATA / 'courses.csv'
OUT_CSV = DATA / 'inferred_prerequisites.csv'

def read_prereqs(path):
    adj = defaultdict(list)
    referenced = set()
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = r.get('course_id')
            p = r.get('prereq_id')
            if c and p:
                adj[c].append(p)
                referenced.add(c)
                referenced.add(p)
    return dict(adj), referenced

def read_courses(path):
    courses = set()
    titles = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            cid = r.get('course_id')
            title = r.get('title')
            if cid:
                courses.add(cid)
                if title:
                    titles[cid] = title
    return courses, titles

# Compute transitive prerequisites for each course using BFS to capture shortest distance
def compute_transitive(adj):
    trans = defaultdict(dict)  # trans[course][prereq] = distance
    for course in set(list(adj.keys()) + [p for vals in adj.values() for p in vals]):
        # BFS from course following prereq edges
        seen = {course: 0}
        q = deque()
        # Start with direct prerequisites
        for p in adj.get(course, []):
            q.append((p, 1))
            if p not in seen or seen[p] > 1:
                seen[p] = 1
        while q:
            node, dist = q.popleft()
            # record
            trans[course][node] = dist
            for p in adj.get(node, []):
                if p not in seen or seen[p] > dist + 1:
                    seen[p] = dist + 1
                    q.append((p, dist + 1))
    return trans


def write_inferred(trans, out_path):
    # flatten to rows and sort
    rows = []
    for c, pres in trans.items():
        for p, d in pres.items():
            rows.append((c, p, d))
    rows.sort()
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['course_id', 'prereq_id', 'distance'])
        for r in rows:
            writer.writerow(r)

if __name__ == '__main__':
    if not PREREQ_CSV.exists():
        print(f"Prerequisites file not found: {PREREQ_CSV}")
        raise SystemExit(1)
    adj, referenced = read_prereqs(PREREQ_CSV)
    courses, titles = (set(), {})
    if COURSES_CSV.exists():
        courses, titles = read_courses(COURSES_CSV)

    missing = [c for c in referenced if c not in courses]
    if missing:
        print("Warning: the following courses referenced in prerequisites.csv are not present in courses.csv:")
        for m in missing:
            print("  ", m)
    else:
        print("All referenced courses present in courses.csv")

    trans = compute_transitive(adj)
    write_inferred(trans, OUT_CSV)
    print(f"Wrote inferred prerequisites to {OUT_CSV}")
    print("Sample (first 20 rows):")
    with open(OUT_CSV, newline='', encoding='utf-8') as f:
        for i, line in enumerate(f):
            print(line.strip())
            if i >= 20:
                break

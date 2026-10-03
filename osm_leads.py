#!/usr/bin/env python3
"""Free lead source: businesses that publish an email in OpenStreetMap.

No API key, no credit, no per-call cost, and it works from a GitHub runner.
This is the bot's first choice; Apify is only called if this comes up short.

The data is volunteered by the businesses and by OSM mappers, so an address
can be stale or mistyped. Everything found here still goes through the same
checks as any other lead before a single email is sent.
"""
import csv
import os
import random
import re
import time

import requests

POOL_FILE = "leads_pool.csv"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]
ATTEMPTS = 2           # these are free public servers: 429 and 504 are normal
BACKOFF_SECONDS = 15
REQUEST_TIMEOUT = 45
# Hard ceiling on the whole hunt. Without it, retries against throttled
# mirrors can grind for hours and hold up the send that follows.
BUDGET_SECONDS = 480
# A real User-Agent is required: Overpass answers 406 without one.
HEADERS = {"User-Agent": "fillo-lead-finder/1.0 (small business outreach)"}
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
DEAD_END = ("careers@", "jobs@", "hr@", "press@", "pr@", "legal@", "no-reply@",
            "noreply@", "privacy@", "abuse@", "webmaster@", "postmaster@")
# Restaurants inside hotel groups: the inbox belongs to a corporate office.
CORPORATE_DOMAINS = {
    "hyatt.com", "marriott.com", "hilton.com", "ihg.com", "accor.com",
    "fourseasons.com", "kimptonhotels.com", "properhotel.com", "thecamby.com",
    "thestanthonyhotel.com", "aol.com",
}

# US and Philippine cities. CAN-SPAM allows business-to-business cold email
# with an opt-out and a postal address; the Philippine Data Privacy Act wants
# the sender identified and an easy way out, which the footer provides.
# Germany, Spain and Canada require consent first, so they stay out.
CITIES = {
    "Austin":       (30.15, -97.95, 30.52, -97.60),
    "Miami":        (25.70, -80.32, 25.86, -80.13),
    "Tampa":        (27.86, -82.55, 28.08, -82.35),
    "Chicago":      (41.76, -87.80, 42.02, -87.55),
    "Nashville":    (36.05, -86.90, 36.25, -86.65),
    "Charlotte":    (35.11, -80.95, 35.35, -80.70),
    "Phoenix":      (33.37, -112.20, 33.70, -111.95),
    "Kansas City":  (38.97, -94.68, 39.20, -94.48),
    "Columbus":     (39.88, -83.10, 40.10, -82.85),
    "San Antonio":  (29.34, -98.65, 29.60, -98.40),
    "Denver":       (39.64, -105.05, 39.80, -104.85),
    "Portland":     (45.45, -122.75, 45.60, -122.55),
    "Orlando":      (28.45, -81.45, 28.62, -81.28),
    "Atlanta":      (33.70, -84.45, 33.85, -84.32),
    "Dallas":       (32.70, -96.90, 32.90, -96.70),
    "Seattle":      (47.55, -122.42, 47.70, -122.28),
    # Philippines
    "Manila":       (14.55, 120.95, 14.65, 121.03),
    "Quezon City":  (14.60, 121.00, 14.76, 121.13),
    "Makati":       (14.53, 121.00, 14.58, 121.05),
    "Taguig":       (14.50, 121.03, 14.58, 121.09),
    "Pasig":        (14.55, 121.05, 14.62, 121.11),
    "Cebu City":    (10.27, 123.85, 10.40, 123.95),
    "Davao City":   (7.03, 125.55, 7.15, 125.65),
    "Baguio":       (16.38, 120.57, 16.45, 120.62),
    "Iloilo City":  (10.68, 122.52, 10.76, 122.60),
}

# OSM tag -> the Category string send_outreach uses to pick a template.
# Every business that has repeat customers is a target (owner's call, 2026-10-03).
GROUPS = [
    ('nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food|ice_cream)$"]', "Restaurant/Cafe"),
    ('nwr["shop"="bakery"]', "Bakery"),
    ('nwr["shop"~"^(hairdresser|barber)$"]', "Barber"),
    ('nwr["shop"~"^(beauty|massage|tattoo)$"]', "Salon/Spa"),
    ('nwr["leisure"="fitness_centre"]', "Pilates"),
    ('nwr["amenity"~"^(dentist|clinic)$"]', "Clinic"),
]


def _query(bbox, group):
    south, west, north, east = bbox
    box = f"{south},{west},{north},{east}"
    return (
        "[out:json][timeout:60];("
        f'{group}["contact:email"]({box});'
        f'{group}["email"]({box});'
        ");out tags 400;"
    )


def _clean_email(raw):
    """OSM emails can carry a mailto: prefix or several addresses."""
    if not raw:
        return None
    first = re.split(r"[;,]", str(raw))[0].strip()
    first = first.replace("mailto:", "").strip()
    if not EMAIL_RE.match(first):
        return None
    if first.lower().startswith(DEAD_END):
        return None
    return first


def fetch_city(city, deadline=None):
    """Return lead dicts for one city. Never raises: a dead endpoint returns []."""
    bbox = CITIES[city]
    found, seen = [], set()

    def out_of_time():
        return deadline is not None and time.time() > deadline

    for group, category in GROUPS:
        if out_of_time():
            print(f"  time budget reached, leaving {city} early")
            break
        body = _query(bbox, group)
        data = None
        for attempt in range(ATTEMPTS):
            for endpoint in ENDPOINTS:
                if out_of_time():
                    break
                try:
                    r = requests.post(endpoint, data={"data": body},
                                      headers=HEADERS, timeout=REQUEST_TIMEOUT)
                    if r.status_code == 200:
                        data = r.json()
                        break
                    print(f"  {endpoint} answered {r.status_code}", flush=True)
                except Exception as e:
                    print(f"  {endpoint} failed: {type(e).__name__}", flush=True)
            if data or out_of_time():
                break
            if attempt < ATTEMPTS - 1:
                print(f"  all mirrors busy, waiting {BACKOFF_SECONDS}s", flush=True)
                time.sleep(BACKOFF_SECONDS)
        if not data:
            print(f"  no answer for this group in {city}", flush=True)
            continue

        for el in data.get("elements", []):
            tags = el.get("tags") or {}
            name = (tags.get("name") or "").strip()
            email = _clean_email(tags.get("contact:email") or tags.get("email"))
            if not name or not email or email.lower() in seen:
                continue
            # Chains and franchises have no local owner to sell to. OSM marks
            # them with a brand tag, which is a cleaner signal than name lists.
            if tags.get("brand") or tags.get("brand:wikidata") or tags.get("operator:wikidata"):
                continue
            if email.split("@")[-1].lower() in CORPORATE_DOMAINS:
                continue
            seen.add(email.lower())
            found.append({
                "Business": name,
                "Email": email,
                "Category": category,
                "Location": city,
            })
        time.sleep(2)  # be polite to a free public service
    return found


def _append(pool_file, rows):
    """Write as we go: a slow mirror must not cost us the cities already done."""
    exists = os.path.exists(pool_file)
    with open(pool_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Business", "Email", "Category", "Location"])
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def generate_leads(limit=60, cities=None, pool_file=POOL_FILE, budget_seconds=BUDGET_SECONDS):
    """Fill the pool from OSM. Returns how many new rows were written."""
    print("=======================================")
    print("   Fillo Lead Finder - OpenStreetMap   ")
    print("=======================================\n")

    known = set()
    if os.path.exists(pool_file):
        with open(pool_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                known.add((row.get("Email") or "").strip().lower())
    for extra in ("fillo_leads.csv", "leads_pool_invalid.csv"):
        if os.path.exists(extra):
            with open(extra, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    known.add((row.get("Email") or "").strip().lower())

    order = cities or random.sample(list(CITIES), len(CITIES))
    deadline = time.time() + budget_seconds
    written = 0
    for city in order:
        if time.time() > deadline:
            print(f"\nTime budget of {budget_seconds}s used up. Stopping with "
                  f"{written} lead(s) saved.", flush=True)
            break
        print(f"Looking up {city}...", flush=True)
        rows = [r for r in fetch_city(city, deadline) if r["Email"].lower() not in known]
        for r in rows:
            known.add(r["Email"].lower())
        if written + len(rows) > limit:
            rows = rows[:limit - written]
        if rows:
            _append(pool_file, rows)   # saved now, not at the end
            written += len(rows)
        print(f"  {len(rows)} new lead(s) from {city} (saved so far {written})", flush=True)
        if written >= limit:
            break

    if not written:
        print("No new leads found in OpenStreetMap this time.")
        return 0

    print(f"\nAdded {written} new lead(s) to {pool_file}.")
    return written


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    where = sys.argv[2:] or None
    generate_leads(limit=n, cities=where)

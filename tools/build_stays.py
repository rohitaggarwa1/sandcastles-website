"""Builds one crawlable page per stay (stays/<slug>/index.html), refreshes the
listing array in index.html, and rewrites sitemap.xml and llms.txt.

Data comes from data/listings.json (exported from Airbnb). Run:
    python3 tools/build_stays.py
"""
import html, json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sandcastlesstays.com"
DATA = json.loads((ROOT / "data/listings.json").read_text())
BY_ID = {d["id"]: d for d in DATA}

# Display order, names, photos and areas for the site. (img, title, city, area, kind, size, airbnbId)
STAYS = [
 (32,"Rivermist · Garden-View 2BHK near Goa Airport","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1808100367006540902"),
 (0,"Oceania · Zuari River View 2BHK","Goa","Rio De Goa, Dabolim","home","2 bedrooms","41844284"),
 (1,"Adora Cabana · Pool-Facing Premium 3BHK","Goa","Adora De Goa, South Goa","home","3 bedrooms","1621848695868234147"),
 (2,"RoDee Casa · Premium Stay with Mountain View & Pool","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1513129553820654329"),
 (4,"Teal Costa · Boho Flat with Pool & Gym","Goa","Vasco da Gama","home","2 bedrooms","1137370569468403227"),
 (5,"Studio Nesto · Cozy Studio near BITS & Airport","Goa","Rio De Goa, Dabolim","home","Studio","1753390048719457262"),
 (7,"Cozy & Serene Stay near Dabolim Airport","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1393221962450225492"),
 (8,"Casa Robo · 9th-Floor Pool View 2BHK","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1628813943680058635"),
 (15,"Zula Azul · Premium 2BHK near Dabolim Airport","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1732454109326961451"),
 (19,"Casa Lang · Premium 2BHK with Washer-Dryer","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1620819206718571226"),
 (21,"Casa Rubra · Pool-Facing 2BHK","Goa","Rio De Goa, Dabolim","home","2 bedrooms","1606425911548303262"),
 (23,"A N A N T · Premium 2BHK with Pool","Goa","Adora De Goa, South Goa","home","2 bedrooms","1775831973911785734"),
 (33,"Garden-View 1BHK near Goa Airport","Goa","Rio De Goa, Dabolim","home","1 bedroom","1808660277697173230"),
 (31,"Casa Sereno · Near Colva Beach & Fatorda","Goa","Margao","home","2 bedrooms","1734832194188995408"),
 (28,"Silverdale · Premium 2BHK","Bengaluru","Horamavu","home","2 bedrooms","1655866296618353043"),
 (26,"Greendale · Stunning 3BHK","Bengaluru","Horamavu","home","3 bedrooms","1655832645721461711"),
 (30,"White House · Bangalore-Themed 4BHK Duplex Villa","Bengaluru","Indiranagar","home","4 bedrooms","1228337197220113744"),
 (17,"Corner House · 3BHK Chic & Cozy House","Bengaluru","Indiranagar","home","3 bedrooms","1084844544875041849"),
 (14,"Malgudi House · Spacious Ethnic 3BHK","Bengaluru","Jayanagar","home","3 bedrooms","1485665764163881676"),
 (24,"Gardenia · Private Garden Luxury 2BHK","Bengaluru","Bengaluru","home","2 bedrooms","1411498650468587712"),
 (10,"Urban Nook 102 · Cozy 1.5BHK","Bengaluru","Horamavu","home","1.5 BHK","1655974485091775929"),
 (12,"Urban Nook 101 · Fully Serviced 1.5BHK","Bengaluru","Horamavu","home","1.5 BHK","1655980256789703610"),
 (11,"Urban Nook 201 · Cozy 1 or 1.5BHK Flat","Bengaluru","Horamavu","home","1.5 BHK","1655967862491698911"),
 (18,"Urban Nook 202 · Affordable 1.5BHK","Bengaluru","Horamavu","home","1.5 BHK","1655915072388339092"),
 (9,"Urban Nook 301 · Bohemian Terrace Studio","Bengaluru","Horamavu","home","Studio","1655898966921201666"),
 (27,"Cozy Corner Room","Bengaluru","Indiranagar","room","Private room","885310383146864691"),
 (20,"Attic Corner · Private AC Ensuite Room with Work Desk","Bengaluru","Indiranagar","room","Private room","885387732231158043"),
 (6,"Red Room · Private Room with Large Bathroom","Bengaluru","Indiranagar","room","Private room","1228332150891129403"),
 (16,"Blue Room · Cozy AC Room, Ground Floor","Bengaluru","Indiranagar","room","Private room","1228335428027829504"),
 (25,"Violet Room","Bengaluru","Indiranagar","room","Private room","1228338849851342645"),
 (3,"Green Lux Room with AC & Balcony","Bengaluru","Indiranagar","room","Private room","1228324784737419403"),
 (13,"Breezy Corner · Room with Balcony","Bengaluru","Indiranagar","room","Private room","1234634311146305320"),
 (22,"Canvas Abode · Boutique 2BHK","Vadodara","Alkapuri","home","2 bedrooms","1614227655910227949"),
 (29,"Thrissur Villa · Private 3BHK for Families","Thrissur","Koorkenchery","home","3 bedrooms","1647893703254378405"),
]
REGION = {"Goa": "Goa", "Bengaluru": "Karnataka", "Vadodara": "Gujarat", "Thrissur": "Kerala"}

# Never publish exact flat numbers, towers or parking slots on the open web.
PRIVATE = [
 (re.compile(r",?\s*Tower\s*\d+[A-Z]?(\s*[-–]\s*\d+)?", re.I), ""),
 (re.compile(r"\bT\d+[-–]\d{3}\b"), ""),
 (re.compile(r"\b\d{1,2}[A-Z]?[-–]\d{3}\b"), ""),
 (re.compile(r"\bP\d[-–]\s?\d+\b"), ""),
 (re.compile(r"\bslot\s+P?\d[\w-]*", re.I), "slot"),
]

def scrub(s):
    for rx, rep in PRIVATE:
        s = rx.sub(rep, s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s+,", ",", s)
    return re.sub(r"[ \t]{2,}", " ", s).strip(" ,-–")

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)

AM_CLEAN = [
 (r":.*$", ""), (r"^(LG|Voltas|Samsung|Whirlpool|Godrej|Haier) refrigerator$", "Refrigerator"),
 (r"^\w+ induction cooker$", "Induction cooker"), (r"^\w+ gas cooker$", "Gas stove"),
 (r"^Fast wifi.*$", "Fast Wi-Fi"), (r"^Wifi$", "Wi-Fi"), (r"^AC$", "Air conditioning"),
 (r"^Free washer.*$", "Washing machine"),
]
def clean_amen(lst):
    out = []
    for a in lst:
        for p, r in AM_CLEAN:
            a = re.sub(p, r, a).strip()
        if a and a not in out:
            out.append(a)
    return out

def stars(r):
    return f"{r:.2f}".rstrip("0").rstrip(".")

def paragraphs(text):
    return [scrub(p) for p in re.split(r"\n\s*\n", text) if p.strip()]

e = lambda s: html.escape(str(s), quote=True)

records = []
for img, title, city, area, kind, size, aid in STAYS:
    d = BY_ID[aid]
    short = title.split(" · ")[0]
    slug = slugify(f"{title} {city}")
    guests = d["g"] or (2 if kind == "room" else 4)
    rec = dict(img=img, title=title, short=short, city=city, area=area, kind=kind, size=size, id=aid,
               slug=slug, url=f"{SITE}/stays/{slug}/", guests=guests, br=d["br"], beds=d["bd"], baths=d["ba"],
               rating=d["r"], reviews=d["n"], lat=d["lat"], lng=d["lng"], summary=paragraphs(d["sum"]),
               hi=[scrub(h) for h in d["hi"] if scrub(h)], faq=d["faq"], near=d["near"],
               amen=clean_amen(d["am"]), views=[v for v in d["views"]])
    records.append(rec)

# ---------- FAQs: listing's own + location/booking basics ----------
def faqs(r):
    place = f"{r['area']}, {r['city']}" if r['city'] not in r['area'] else r['area']
    base = [
        (f"Where is {r['short']} located?",
         f"{r['short']} is in {place}, {REGION[r['city']]}, India. The exact address is shared by Airbnb after booking."
         + (" It is about 10 minutes from Goa International Airport (Dabolim) and BITS Pilani Goa." if "Dabolim" in r['area'] or "Rio De Goa" in r['area'] else "")),
        (f"How many guests can stay at {r['short']}?",
         f"Up to {r['guests']} guests. It has {r['size'].lower()}"
         + (f" with {r['beds']} bed{'s' if r['beds'] != 1 else ''} and {r['baths']:g} bathroom{'s' if r['baths'] != 1 else ''}." if r['beds'] else ".")),
        (f"How do I book {r['short']}?",
         "Book directly on Airbnb, where you can see live prices, availability and all guest reviews, and pay securely."),
    ]
    seen, out = set(), []
    for q, a in base + [(scrub(q), scrub(a)) for q, a in r["faq"]]:
        ql = q.lower()
        topic = next((t for t in ("guest", "book", "located", "exact location") if t in ql), None)
        k = topic or re.sub(r"\W", "", ql)[:40]
        if k in seen or not a:
            continue
        seen.add(k); out.append((q, a))
    return out[:9]

# ---------- page template ----------
CSS = """
:root{--navy:#14213a;--gold:#c49a4a;--gold-soft:#e6cf9d;--sand:#f7f2e8;--card:#fffdf8;--line:#e5dccb;--ink:#1a2236;--muted:#5f6779;
--bg:var(--sand);--fg:var(--ink);--f-display:"Playfair Display",Georgia,serif;--f-caps:"Marcellus",Georgia,serif;--f-body:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0e1626;--fg:#ece4d4;--card:#16213a;--line:#2a3854;--muted:#a3aabb;--ink:#ece4d4;--gold:#d6ae62;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0e1626;--fg:#ece4d4;--card:#16213a;--line:#2a3854;--muted:#a3aabb;--ink:#ece4d4;--gold:#d6ae62;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:400 16px/1.65 var(--f-body);-webkit-font-smoothing:antialiased}
a{color:inherit}img{max-width:100%}
.wrap{max-width:1040px;margin:0 auto;padding-inline:max(16px,env(safe-area-inset-left,0px))}
.top{background:var(--navy);border-bottom:1px solid rgba(196,154,74,.25)}
.top .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-block:12px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:#f3ead8}
.brand svg{width:34px;height:34px}.brand b{font:400 .95rem/1 var(--f-caps);letter-spacing:.22em}
.top nav{display:flex;gap:18px;font-size:.9rem}.top nav a{color:#b9bfcc;text-decoration:none}.top nav a:hover{color:#f3ead8}
.crumbs{font-size:.85rem;color:var(--muted);margin:22px 0 10px}.crumbs a{color:var(--muted)}
h1,h2{font-family:var(--f-display);font-weight:600;line-height:1.15;margin:0}
h1{font-size:clamp(1.8rem,4.4vw,2.7rem);text-wrap:balance}
h2{font-size:1.45rem;margin:40px 0 14px}
.sub{color:var(--muted);margin:8px 0 18px}
.hero{border-radius:14px;overflow:hidden;aspect-ratio:16/9;background:var(--line);margin-bottom:20px}
.hero img{width:100%;height:100%;object-fit:cover;display:block}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px;padding:0;list-style:none}
.facts li{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:.45em .9em;font-size:.9rem}
.cta{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:8px 0 6px}
.btn{display:inline-flex;align-items:center;gap:.4em;font:700 .95rem/1 var(--f-body);padding:.95em 1.4em;border-radius:999px;text-decoration:none;background:var(--gold);color:#14213a}
.btn.alt{background:transparent;border:1px solid var(--line);color:var(--fg)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:6px 28px;padding:0;margin:0;list-style:none}
.cols li{padding:6px 0;border-bottom:1px solid var(--line);font-size:.95rem}
@media (max-width:640px){.cols{grid-template-columns:1fr}}
table{border-collapse:collapse;width:100%;max-width:520px}td{padding:8px 0;border-bottom:1px solid var(--line)}td+td{text-align:right;color:var(--muted)}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:10px}
summary{font-weight:700;cursor:pointer}details p{margin:8px 0 0;color:var(--muted)}
.more{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.more a{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none}
.more img{aspect-ratio:16/10;height:auto;object-fit:cover;width:100%;display:block}.more span{display:block;padding:10px 12px;font-weight:600;font-size:.92rem}
footer{background:var(--navy);color:#b9bfcc;font-size:.85rem;margin-top:64px}footer .wrap{padding-block:24px;display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between}
footer a{color:#e6cf9d;text-decoration:none}
"""

LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true" style="color:#c49a4a"><path fill="currentColor" d="M25 16h3v2.5h2V16h3v2.5h2V16h3v10h-13zM14 27h3v2.5h2V27h3v2.5h2V27h2v-1h12v1h2v2.5h2V27h3v2.5h2V27h3v20H14z"/><path fill="#14213a" d="M28 47v-7a4 4 0 0 1 8 0v7z"/><path d="M4 51c8-3 14-3 22 0s16 3 34-1" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>'

def jsonld(r, fq):
    desc = " ".join(r["summary"])[:500]
    amen = [{"@type": "LocationFeatureSpecification", "name": a, "value": True} for a in r["amen"][:20]]
    place = {"@type": "Accommodation", "additionalType": "EntirePlace" if r["kind"] == "home" else "PrivateRoom",
             "numberOfBedrooms": r["br"], "numberOfBathroomsTotal": r["baths"],
             "occupancy": {"@type": "QuantitativeValue", "value": r["guests"]}, "amenityFeature": amen}
    if r["beds"]:
        place["bed"] = {"@type": "BedDetails", "numberOfBeds": r["beds"]}
    vr = {"@context": "https://schema.org", "@type": "VacationRental", "@id": r["url"] + "#rental",
          "name": r["title"], "identifier": r["id"], "url": r["url"],
          "sameAs": f"https://www.airbnb.co.in/rooms/{r['id']}",
          "description": desc, "image": [f"{SITE}/img/{r['img']:02d}.jpg"],
          "brand": {"@type": "Organization", "name": "Sandcastles Stays", "url": SITE + "/"},
          "address": {"@type": "PostalAddress", "addressLocality": r["area"].split(", ")[-1] if r["city"] == "Goa" else r["city"],
                      "addressRegion": REGION[r["city"]], "addressCountry": "IN"},
          "latitude": r["lat"], "longitude": r["lng"], "containsPlace": place,
          "checkinTime": "14:00", "checkoutTime": "11:00", "knowsLanguage": ["en", "hi"]}
    if r["reviews"] > 0 and r["rating"] > 0:
        vr["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": r["rating"], "ratingCount": r["reviews"], "bestRating": 5}
    faqld = {"@context": "https://schema.org", "@type": "FAQPage",
             "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in fq]}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Sandcastles Stays", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": f"Stays in {r['city']}", "item": SITE + "/#stays"},
        {"@type": "ListItem", "position": 3, "name": r["short"], "item": r["url"]}]}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return "\n".join(f'<script type="application/ld+json">\n{dump(o)}\n</script>' for o in (vr, faqld, crumbs))

def page(r):
    fq = faqs(r)
    air = f"https://www.airbnb.co.in/rooms/{r['id']}"
    place = r["area"] if r["city"] in r["area"] else f"{r['area']}, {r['city']}"
    meta = f"{r['title']} in {place}: {r['size'].lower()}, up to {r['guests']} guests"
    meta += f", rated {stars(r['rating'])}★ from {r['reviews']} reviews." if r["reviews"] else ". New on Airbnb."
    meta += " Hosted by Sandcastles Stays. Book on Airbnb."
    facts = [r["size"], f"Up to {r['guests']} guests"]
    if r["beds"]: facts.append(f"{r['beds']} bed{'s' if r['beds'] != 1 else ''}")
    facts.append(f"{r['baths']:g} bath{'s' if r['baths'] != 1 else ''}")
    facts.append(f"★ {stars(r['rating'])} ({r['reviews']} reviews)" if r["reviews"] else "New listing")
    near = "".join(f"<tr><td>{e(n)}</td><td>{e(t)}</td></tr>" for n, t in r["near"])
    others = [o for o in records if o["city"] == r["city"] and o["id"] != r["id"]][:6]
    more = "".join(f'<a href="/stays/{o["slug"]}/"><img src="/img/{o["img"]:02d}.jpg" alt="{e(o["title"])}" loading="lazy" width="720" height="406"><span>{e(o["title"])}</span></a>' for o in others)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(r['title'])} · {e(place)} | Sandcastles Stays</title>
<meta name="description" content="{e(meta)}">
<link rel="canonical" href="{r['url']}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(r['title'])}">
<meta property="og:description" content="{e(meta)}">
<meta property="og:image" content="{SITE}/img/{r['img']:02d}.jpg">
<meta property="og:url" content="{r['url']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Marcellus&family=Manrope:wght@400;600;700&display=swap">
<style>{CSS}</style>
{jsonld(r, fq)}
</head>
<body>
<header class="top"><div class="wrap">
 <a class="brand" href="/">{LOGO}<b>SANDCASTLES</b></a>
 <nav aria-label="Main"><a href="/#stays">All stays</a><a href="/owners/">List your home</a><a href="/#contact">Contact</a></nav>
</div></header>
<main class="wrap">
 <p class="crumbs"><a href="/">Home</a> › <a href="/#stays">Stays in {e(r['city'])}</a> › {e(r['short'])}</p>
 <h1>{e(r['title'])}</h1>
 <p class="sub">{e(place)}, {REGION[r['city']]}, India · {'Entire home' if r['kind'] == 'home' else 'Private room in a shared home'} · Hosted by Sandcastles Stays</p>
 <div class="hero"><img src="/img/{r['img']:02d}.jpg" alt="{e(r['title'])}" width="720" height="406"></div>
 <ul class="facts">{''.join(f'<li>{e(f)}</li>' for f in facts)}</ul>
 <div class="cta"><a class="btn" href="{air}" target="_blank" rel="noopener">Check prices &amp; book on Airbnb ↗</a><a class="btn alt" href="https://wa.me/918072770364?text={e('Hi Sandcastles, I have a question about ' + r['short'])}" target="_blank" rel="noopener">Ask us on WhatsApp</a></div>

 <h2>About this stay</h2>
 {''.join(f'<p>{e(p)}</p>' for p in r['summary'])}
 {f'<h2>Highlights</h2><ul class="cols">' + ''.join(f'<li>{e(h)}</li>' for h in r['hi']) + '</ul>' if r['hi'] else ''}
 {f'<h2>Nearby</h2><table>{near}</table>' if near else ''}
 <h2>Amenities</h2>
 <ul class="cols">{''.join(f'<li>{e(a)}</li>' for a in r['amen'])}</ul>
 <h2>Frequently asked questions</h2>
 {''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in fq)}
 <div class="cta" style="margin-top:22px"><a class="btn" href="{air}" target="_blank" rel="noopener">See live availability on Airbnb ↗</a></div>
 {f'<h2>More stays in {e(r["city"])}</h2><div class="more">{more}</div>' if more else ''}
</main>
<footer><div class="wrap"><span>© 2026 Sandcastles Stays · Airbnb property management across India</span><span><a href="/">Home</a> · <a href="/owners/">For owners</a> · <a href="https://www.instagram.com/sandcastlesstays/" target="_blank" rel="noopener">Instagram</a></span></div></footer>
</body>
</html>
"""

for r in records:
    out = ROOT / "stays" / r["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(r))

# ---------- homepage listing array + static (crawlable) grid ----------
idx = (ROOT / "index.html").read_text()
arr = ",\n".join(
    f' [{r["img"]},{json.dumps(r["title"], ensure_ascii=False)},"{r["city"]}",{json.dumps(r["area"])},"{r["kind"]}","{r["size"]}",{r["rating"] or 0},{r["reviews"]},"{r["id"]}","{r["slug"]}"]'
    for r in records)
idx = re.sub(r"const S = \[.*?\n\];", "const S = [\n // [img, title, city, area, kind, size, rating, reviews, airbnbId, slug]\n" + arr + "\n];", idx, flags=re.S)

def card(r):
    rate = f'<i>★</i> {stars(r["rating"])} <small>({r["reviews"]})</small>' if r["reviews"] else '<span class="new">New</span>'
    return (f'<a class="stay" href="/stays/{r["slug"]}/"><div class="ph"><img loading="lazy" src="img/{r["img"]:02d}.jpg" alt="{e(r["title"])}"><span class="tag">{r["city"]}</span></div>'
            f'<div class="body"><div class="meta"><span>{e(r["area"])} · {r["size"]}</span><span class="rate">{rate}</span></div><h3>{e(r["title"])}</h3>'
            f'<span class="go">View details <span aria-hidden="true">→</span></span></div></a>')
static = "\n".join(card(r) for r in records)
new_grid = '<div class="grid" id="grid"><!--static-->\n' + static + '\n<!--/static--></div>'
idx, n = re.subn(r'<div class="grid" id="grid">(?:<!--static-->.*?<!--/static-->)?</div>', lambda m: new_grid, idx, flags=re.S)
assert n == 1, "grid placeholder not found"
(ROOT / "index.html").write_text(idx)

# ---------- sitemap + llms.txt ----------
today = "2026-11-02"
urls = [f"{SITE}/", f"{SITE}/owners/", f"{SITE}/shop/"] + [r["url"] for r in records]
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")

lines = ["# Sandcastles Stays", "",
 f"> Sandcastles Stays is a small, founder-run Airbnb hosting and property-management company in India, run by Rohit and Deepika. It hosts {len(records)} stays in Goa (Dabolim, Rio De Goa, Adora De Goa, Vasco, Margao), Bengaluru (Indiranagar, Horamavu, Jayanagar), Vadodara and Thrissur, and manages homes for owners anywhere in India on a 70:30 profit share (owner 70%).",
 "", "All bookings are made on Airbnb. Host profile: https://www.airbnb.co.in/users/show/153546484",
 "Contact: +91 80727 70364 (phone/WhatsApp), Instagram @sandcastlesstays", "",
 "## For homeowners", f"- [List your home with Sandcastles]({SITE}/owners/): set-up, listing, pricing, guests, cleaning and monthly owner reports.", ""]
for c in ["Goa", "Bengaluru", "Vadodara", "Thrissur"]:
    lines.append(f"## Stays in {c}")
    for r in [x for x in records if x["city"] == c]:
        rt = f", {stars(r['rating'])}★ ({r['reviews']} reviews)" if r["reviews"] else ", new"
        lines.append(f"- [{r['title']}]({r['url']}): {r['size']}, {r['area']}, up to {r['guests']} guests{rt}")
    lines.append("")
(ROOT / "llms.txt").write_text("\n".join(lines))
print(len(records), "stay pages built")

# Sandcastles Stays website

Live at https://sandcastlesstays.com (hosted on Netlify, deploys from this repo).

- `index.html` — the whole site (listings data is the `S` array near the bottom)
- `img/` — listing photos
- `stays/<slug>/` — one crawlable page per stay (FAQ + schema.org VacationRental data), generated
- `data/listings.json` + `tools/build_stays.py` — listing data exported from Airbnb and the generator. Run `python3 tools/build_stays.py` to rebuild stay pages, the homepage list, `sitemap.xml` and `llms.txt`
- `llms.txt` — plain-text summary of the business and every stay, for AI assistants

# Seattle School Zones (test)

An experiment: the [NYC School Zones](https://nycschoolzones.com) map
([nycschoolzones/nycschoolzones](https://github.com/nycschoolzones/nycschoolzones)) running on Seattle Public Schools'
data. It asks one question: how much of the NYC map survives a move to another city?

It is a test, not a finished site. Nothing here is checked the way the NYC map is.

## What it shows

- Elementary, middle and high school attendance areas for 2025-26.
- The schools without an attendance area (option schools and the two Highly Capable schools) as their own markers.
- Each school's spring 2026 Smarter Balanced ELA and math results, as the Color by modes and on the card.
- Each option school's GeoZone (the area whose residents get a tiebreaker there): outlined when you open the school, and listed on a zone's card for the spot you clicked or the address you searched.
- Links from each school's card to its profile on seattleschools.org and its Washington State Report Card.
- Address search for Seattle.

Not here yet: a page per school, enrollment and demographics, and anything about how School Choice works beyond a link to the district.

## Build

No framework and no npm; Python 3 and one HTML template.

```sh
python3 scripts/fetch_seattle.py   # data/*.json from the sources below
python3 scripts/build.py           # index.html and assets/
python3 -m http.server 8000        # preview at http://localhost:8000
```

## Repo layout

```
src/template.html          the map: styles, markup and one script. CITY (top of the script) holds the per-city settings
scripts/fetch_seattle.py   downloads the data
scripts/build.py           data + template -> index.html, assets/ms.js, assets/hs.js
scripts/settings.py        the data year labels and color ramps the build fills into the template
data/elem_zones.json       attendance areas and their schools, one file per level (ms_zones.json, hs_zones.json)
data/option_schools.json   schools without an attendance area, per level
data/geo_zones.json        option schools' GeoZones
data/school_links.json     each school's profile page on seattleschools.org and its state id
data/results.json          state test results per school
index.html, assets/        built output, committed so the page can be served as-is
brand/, icons/, preview.png, scripts/make_brand.py, scripts/make_preview.py   still the NYC site's
ARCHITECTURE.md            the NYC code map, with a section on what changed here
```

## Data sources

| What | Source |
| - | - |
| Attendance areas, GeoZones, school sites | Seattle Public Schools' public ArcGIS services (`services2.arcgis.com/I7NQBinfvOmxQbXs`) |
| School profile pages | Seattle Public Schools' [school directory](https://www.seattleschools.org/schools/) |
| Test results | Washington State Report Card assessment data, 2025-26 ([data.wa.gov](https://data.wa.gov/)) |
| Basemap tiles and address search | King County GIS (`gismaps.kingcounty.gov`) |

Each school's profile page links to its district dashboard and its state report card, so it carries both the
district's id and the state's. `fetch_seattle.py` reads them there (`links()`) and matches test results by id. The
state holds back counts for three schools on the map (Cascadia, Decatur, The Center School). Cascade Virtual Option
has no link or results: the district's page for it carries the Cascade Parent Partnership's ids.

## License

Copyright (C) 2026 NYC School Zones

The code and design are licensed under the [GNU Affero General Public License v3.0 or later](LICENSE). The data is not
covered by this license and isn't ours to license; it belongs to the sources above.

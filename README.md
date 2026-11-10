# Seattle School Zones (test)

An experiment: the [NYC School Zones](https://nycschoolzones.com) map
([nycschoolzones/nycschoolzones](https://github.com/nycschoolzones/nycschoolzones)) running on Seattle Public Schools'
data. It asks one question: how much of the NYC map survives a move to another city?

It is a test, not a finished site. Nothing here is checked the way the NYC map is.

## What it shows

- Elementary, middle and high school attendance areas for 2025-26.
- The schools without an attendance area (option schools and the two Highly Capable schools) as their own markers.
- Each school's spring 2026 Smarter Balanced ELA and math results, as the Color by modes and on the card.
- Address search for Seattle.

Not here yet: a page per school, the option schools' GeoZone outlines (downloaded, not drawn), enrollment and
demographics, and anything about how School Choice works beyond a link to the district.

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
data/geo_zones.json        option schools' GeoZones (not drawn yet)
data/results.json          state test results per school
index.html, assets/        built output, committed so the page can be served as-is
brand/, icons/, preview.png, scripts/make_brand.py, scripts/make_preview.py   still the NYC site's
ARCHITECTURE.md            the NYC code map, with a section on what changed here
```

## Data sources

| What | Source |
| - | - |
| Attendance areas, GeoZones, school sites | Seattle Public Schools' public ArcGIS services (`services2.arcgis.com/I7NQBinfvOmxQbXs`) |
| Test results | Washington State Report Card assessment data, 2025-26 ([data.wa.gov](https://data.wa.gov/)) |
| Basemap tiles and address search | King County GIS (`gismaps.kingcounty.gov`) |

Schools are matched between the district's and the state's files by name (`name_key` and `ALIASES` in
`fetch_seattle.py`); the fetch prints the ones it couldn't match. The state holds back counts for three schools on the
map (Cascadia, Decatur, The Center School), and Cascade Virtual Option isn't in its file under that name, so those four
have no results.

## License

Copyright (C) 2026 NYC School Zones

The code and design are licensed under the [GNU Affero General Public License v3.0 or later](LICENSE). The data is not
covered by this license and isn't ours to license; it belongs to the sources above.

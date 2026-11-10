# Copyright (C) 2026 NYC School Zones · SPDX-License-Identifier: AGPL-3.0-or-later
"""Settings shared by the map (src/template.html, filled in by build.py), the school, district and neighborhood
pages (pages.py, neighborhoods.py) and fetch_data.py. Change a value here and rebuild; don't copy it elsewhere."""

# ---------- which year's data the site shows ----------

# School Quality Snapshot: ratings, programs, high school outcomes (and charter schools' test scores). "2025" is the 2024-25 school year
# (its address on tools.nycenet.edu/snapshot/2025/...).
SNAPSHOT_YEAR = "2025"
SNAPSHOT_LABEL = f"{int(SNAPSHOT_YEAR) - 1}–{SNAPSHOT_YEAR[2:]}"   # "2024–25"
# State ELA and math test scores (data/state_tests.json): the DOE's school results on InfoHub, a year ahead of the
# Snapshot. TESTS_YEAR is the spring the tests were taken. Charter schools aren't in that file, so theirs (and any
# school missing from it) still come from the Snapshot and say so.
TESTS_YEAR = "2026"
TESTS_LABEL = f"spring {TESTS_YEAR}"
# NYC-wide share meeting standards in grades 3-5 that spring (%), from the DOE's citywide results, quoted on the map
CITY_ELA_ES = 47
CITY_MATH_ES = 60
# A note on that year's scores, next to them on the map and the school pages; "" for none. Spring 2026: grades 3-5
# ELA jumped in 2025 (the state lowered the grade 3, 4 and 6 cut scores) and fell back in 2026 to about its 2023-24
# level (citywide grade 3: 2024 ~46%, 2025 58%, 2026 44%). TESTS_NOTE_SHORT goes on each elementary school's card.
TESTS_NOTE = ""
TESTS_NOTE_SHORT = ""
# Pre-K and 3-K seats and applicants: the DOE's Local Law 72 admissions report (data/prek.json)
PREK_LABEL = "fall 2025"
# MySchools directories (data/ms_directory.json, hs_directory.json, k_priority.json): the admissions round their
# "last year" seats, applicants and priority groups describe. The 2026-27 directories report fall 2026 admissions;
# fetch_data.py warns when a download's school year doesn't match.
MYSCHOOLS_LABEL = "fall 2026"
# Building use: the SCA's Enrollment, Capacity & Utilization Report ("Blue Book", data/utilization.json)
BLUE_BOOK_LABEL = "2025–26"
# Race and ethnicity, family income and more: the state's Report Card enrollment data (data/enrollment.json), the
# school year it counts. The build stops if the file is from another year.
DEMOGRAPHICS_LABEL = "2025–26"

# NYC-wide high school averages from that Snapshot, quoted next to each school's numbers
CITY_GRAD = 81        # 4-year graduation rate, %
CITY_READINESS = 54   # college readiness score, of 100

# ---------- color ramps ----------

# [value, color name] stops, low (red) to high (green). The map's Color by modes, legends and card bars use them,
# and so do the tables and bars on the generated pages. Each theme has its own colors for the names:
# light is bright and light, so dark map labels read well on top of the zone fills, and steps down in lightness
# red < teal < orange < yellow so neighboring levels stay apart for red-green color blindness (checked by simulation).
RAMP_COLORS = {"light": {"red": [228, 68, 73], "orange": [249, 140, 16], "yellow": [255, 226, 110], "green": [53, 182, 156]},
               "dark": {"red": [184, 32, 42], "orange": [232, 116, 42], "yellow": [247, 207, 69], "green": [31, 138, 132]}}
# DOE ratings: 1 -> 5, 2 -> 50, 3 -> 75, 4 -> 95 on this scale
RATE_STOPS = [[5, "red"], [50, "orange"], [75, "yellow"], [95, "green"]]
# % meeting state standards
TEST_STOPS = [[10, "red"], [50, "yellow"], [90, "green"]]
# high school outcomes
OUT_STOPS = {"grad": [[65, "red"], [80, "yellow"], [95, "green"]],     # 4-year graduation rate (%)
             "coll": [[40, "red"], [60, "yellow"], [80, "green"]],     # college or career program (%)
             "ccr": [[35, "red"], [55, "yellow"], [80, "green"]],      # college readiness score
             "sat": [[800, "red"], [950, "yellow"], [1200, "green"]]}  # average SAT

# Race and ethnicity bars on the cards and school pages: [label, color], in the order of an enrollment.json row
# (fetch_seattle.py ENROLLMENT_FIELDS). Categorical (no group is "better"), so none of the ramp colors above. The first
# four and the gray were checked for color blindness side by side on the NYC site; the purple was added here and wasn't.
# An optional third item is the name in the section's one-line summary, where the label's first word won't do.
DEMO_GROUPS = [["Asian", "#2a78d6"], ["Black", "#eb6834"], ["Hispanic or Latino", "#1baf7a"], ["White", "#eda100"],
               ["Two or more races", "#8a63c9", "multiracial"], ["Native American or Pacific Islander", "#9aa5a0"]]

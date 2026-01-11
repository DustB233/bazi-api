# make_city_dict.py
from __future__ import annotations
from pathlib import Path
import re

# GeoNames columns for cities*.txt:
# 0 geonameid
# 1 name
# 2 asciiname
# 3 alternatenames
# 4 latitude
# 5 longitude
# 6 feature class
# 7 feature code
# 8 country code (ISO2)
# ...
# 14 population
# ...
#
# We will generate keys: "<city>,<country>" in lowercase,
# values: (lon, lat) floats (note GeoNames stores lat then lon)

# Map ISO2 country code -> the label YOU want in the key
ISO2_TO_LABEL = {
    "CN": "china",
    "TW": "taiwan",
    "HK": "china",   # Hong Kong in your scheme
    "MO": "china",   # Macau in your scheme
    "US": "usa",
    "GB": "uk",
    "SG": "singapore",
    # Add more if you want:
    # "CA": "canada",
    # "AU": "australia",
    # "JP": "japan",
    # "KR": "korea",
    # "FR": "france",
    # ...
}

def norm_city(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s

def load_geonames(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 15:
                continue
            asciiname = parts[2]
            lat = parts[4]
            lon = parts[5]
            iso2 = parts[8]
            pop = parts[14]
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                pop_i = int(pop) if pop else 0
            except:
                continue
            rows.append((asciiname, iso2, lon_f, lat_f, pop_i))
    return rows

def build_top_n(rows, n: int = 1000):
    # Convert iso2 -> label; skip countries not in mapping
    filtered = []
    for asciiname, iso2, lon, lat, pop in rows:
        label = ISO2_TO_LABEL.get(iso2)
        if not label:
            continue
        city = norm_city(asciiname)
        if not city:
            continue
        key = f"{city},{label}"

        filtered.append((key, lon, lat, pop))

    # Sort by population desc
    filtered.sort(key=lambda x: x[3], reverse=True)

    # Deduplicate by key (keep highest population)
    out = {}
    for key, lon, lat, pop in filtered:
        if key in out:
            continue
        out[key] = (lon, lat)
        if len(out) >= n:
            break
    return out

def dump_python_dict(d: dict[str, tuple[float, float]]) -> str:
    # Pretty-ish formatting
    lines = ["_CITY_LONLAT = {"]
    for k, (lon, lat) in d.items():
        lines.append(f'    "{k}": ({lon:.6f}, {lat:.6f}),')
    lines.append("}")
    return "\n".join(lines)

if __name__ == "__main__":
    # Change this to your file name:
    # cities5000.txt or cities15000.txt
    geonames_file = Path("cities15000.txt")

    if not geonames_file.exists():
        raise SystemExit(f"Missing file: {geonames_file.resolve()}")

    rows = load_geonames(geonames_file)
    city_dict = build_top_n(rows, n=15000)
    print(dump_python_dict(city_dict))

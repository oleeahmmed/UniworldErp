"""
Loads Bangladesh district/upazila/Dhaka-city-area reference data from
static/images/location/ and exposes it in a form convenient for:

- Populating City/Area dropdowns on the customer create/edit form
  (cascading: Area choices depend on the selected City).
- Validating CustomerVendor.city / CustomerVendor.area values.

City == district name (e.g. "Dhaka", "Chattogram", "Narayanganj").
Area == thana/upazila name within that city/district.
"""

import json
import os
from functools import lru_cache

from django.conf import settings


LOCATION_DIR = os.path.join(settings.BASE_DIR, 'static', 'images', 'location')


def _load_json(filename):
    with open(os.path.join(LOCATION_DIR, filename), encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_city_area_map():
    """Returns an ordered dict: city name -> sorted list of area names."""
    districts = _load_json('bd-districts.json')['districts']
    upazilas = _load_json('bd-upazilas.json')['upazilas']
    dhaka_areas = _load_json('dhaka-city.json')['dhaka']

    district_by_id = {d['id']: d['name'] for d in districts}

    city_areas = {d['name']: set() for d in districts}

    for u in upazilas:
        city_name = district_by_id.get(u['district_id'])
        if city_name:
            city_areas[city_name].add(u['name'])

    for entry in dhaka_areas:
        city_areas['Dhaka'].add(entry['name'])

    return {city: sorted(areas) for city, areas in sorted(city_areas.items())}


@lru_cache(maxsize=1)
def get_city_choices():
    """Returns [(city, city), ...] sorted alphabetically, for a ChoiceField."""
    return [(city, city) for city in get_city_area_map().keys()]


@lru_cache(maxsize=1)
def get_area_choices():
    """Returns [(area, area), ...] - the union of every area across all cities,
    deduplicated and sorted, for a ChoiceField that validates any valid area
    regardless of which city is currently selected."""
    areas = set()
    for area_list in get_city_area_map().values():
        areas.update(area_list)
    return [(area, area) for area in sorted(areas)]

"""
Django management command to backfill the new CustomerVendor.city and
CustomerVendor.area fields by matching keywords found in the existing free-text
CustomerVendor.address field against the Bangladesh location data in
static/images/location/ (bd-districts.json, bd-upazilas.json, dhaka-city.json).

The address field itself is never modified - this only fills city/area.
Re-running this command is safe (idempotent): it always re-derives city/area
from the current address text.

Usage:
    # Preview changes (safe, nothing is saved):
    python manage.py backfill_customer_city_area --dry-run

    # Apply for real:
    python manage.py backfill_customer_city_area

    # Show the most common addresses that didn't match anything,
    # useful for extending AREA_ALIASES / DISTRICT_ALIASES:
    python manage.py backfill_customer_city_area --dry-run --show-unmatched
"""

import json
import os
import re
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand

from uniworlderp.models import CustomerVendor


LOCATION_DIR = os.path.join(settings.BASE_DIR, 'static', 'images', 'location')

# Spelling variants seen in real address data, mapped to the canonical
# district name used in bd-districts.json.
DISTRICT_ALIASES = {
    'ctg': 'Chattogram',
    'chittagong': 'Chattogram',
    'chattagram': 'Chattogram',
    'chottogram': 'Chattogram',
    'b.baria': 'Brahmanbaria',
    'brahman baria': 'Brahmanbaria',
    'narayan ganj': 'Narayanganj',
}

# Spelling variants seen in real address data, mapped to the canonical
# area/thana name used in dhaka-city.json or bd-upazilas.json.
AREA_ALIASES = {
    'bangshal': 'Bongshal',
    'bongshall': 'Bongshal',
    'bhoirob': 'Bhairab',
    'bhoirab': 'Bhairab',
    'jattarabari': 'Jatrabari',
    'nababgonj': 'Nababganj',
    'nobabgonj': 'Nababganj',
    'nobabpur': 'Nababganj',
    'nawabpur': 'Nababganj',
    'malibag': 'Malibagh',
    'kamrangir char': 'Kamrangirchar',
    'siddiqbazar': 'Kotwali',
    'siddiqbazaar': 'Kotwali',
    'siddique bazar': 'Kotwali',
    'siddiq bazar': 'Kotwali',
    'siddque bazar': 'Kotwali',
    'siddikbazar': 'Kotwali',
    'kawranbazar': 'Tejgaon',
    'kawran bazar': 'Tejgaon',
    'chockbazar': 'Chawkbazar',
    'chuk bazar': 'Chawkbazar',
    'gabtoly': 'Gabtoli',
    'siddir gonj': 'Siddhirganj',
    'kodomtoly': 'Kadamtoli',
    'kodomtoli': 'Kadamtoli',
    'mogbazar': 'Moghbazar',
    'mog bazar': 'Moghbazar',
    'kaptan bazar': 'Motijheel',
    'basila': 'Mohammadpur',
    'bosila': 'Mohammadpur',
    'bochila': 'Mohammadpur',
    'agamasi lane': 'Kotwali',
    'agamachi lane': 'Kotwali',
    'nababpur': 'Nababganj',
    'nobabganj': 'Nababganj',
    'chok bazar': 'Chawkbazar',
    'karwon bazar': 'Tejgaon',
    'noya bazar': 'Nayabazar',
}

# Upazila names that exist under more than one district (ambiguous without
# extra context). Skip these for area matching to avoid mis-assigning a city.
AMBIGUOUS_AREA_NAMES = {
    'Nawabganj', 'Lohagara', 'Pirganj', 'Durgapur', 'Daulatpur',
    'Kaliganj', 'Phulbari', 'Kachua', 'Shibganj', 'Kaukhali',
}


def _load_json(filename):
    with open(os.path.join(LOCATION_DIR, filename), encoding='utf-8') as f:
        return json.load(f)


def _name_to_pattern(name):
    """Build a case-insensitive regex matching `name`, tolerant of
    extra spaces/hyphens between words (e.g. 'Mirpur-10' vs 'Mirpur 10')."""
    parts = re.split(r'[\s\-]+', name.strip())
    escaped = [re.escape(p) for p in parts if p]
    body = r'[\s\-]*'.join(escaped)
    return re.compile(r'\b' + body + r'\b', re.IGNORECASE)


def build_candidates():
    """Returns (area_candidates, district_candidates).

    area_candidates: list of (regex, area_name, city_name), longest names first.
    district_candidates: list of (regex, city_name), longest names first.
    """
    districts = _load_json('bd-districts.json')['districts']
    upazilas = _load_json('bd-upazilas.json')['upazilas']
    dhaka_areas = _load_json('dhaka-city.json')['dhaka']

    district_by_id = {d['id']: d['name'] for d in districts}

    # Count upazila name occurrences across districts to detect ambiguity
    name_counts = Counter(u['name'] for u in upazilas)

    area_entries = []  # (area_name, city_name)

    # Dhaka metro thana/area names -> city = Dhaka
    seen_dhaka = set()
    for entry in dhaka_areas:
        name = entry['name']
        if name in seen_dhaka:
            continue
        seen_dhaka.add(name)
        area_entries.append((name, 'Dhaka'))

    # Upazilas -> city = their district name
    for u in upazilas:
        name = u['name']
        if name in AMBIGUOUS_AREA_NAMES or name_counts[name] > 1:
            continue
        city_name = district_by_id.get(u['district_id'])
        if not city_name:
            continue
        area_entries.append((name, city_name))

    # Longer names first so "Mirpur-10" matches before "Mirpur"
    area_entries.sort(key=lambda x: len(x[0]), reverse=True)
    area_candidates = [(_name_to_pattern(name), name, city) for name, city in area_entries]

    district_entries = sorted(districts, key=lambda d: len(d['name']), reverse=True)
    district_candidates = [(_name_to_pattern(d['name']), d['name']) for d in district_entries]

    return area_candidates, district_candidates


def _apply_aliases(text, aliases):
    for variant, canonical in aliases.items():
        pattern = _name_to_pattern(variant)
        text = pattern.sub(canonical, text)
    return text


def match_city_area(address, area_candidates, district_candidates):
    """Return (city, area) derived from the given address text, or (None, None)."""
    if not address:
        return None, None

    text = _apply_aliases(address, AREA_ALIASES)
    text = _apply_aliases(text, DISTRICT_ALIASES)

    for pattern, area_name, city_name in area_candidates:
        if pattern.search(text):
            return city_name, area_name

    for pattern, city_name in district_candidates:
        if pattern.search(text):
            return city_name, None

    return None, None


class Command(BaseCommand):
    help = (
        'Backfills CustomerVendor.city and CustomerVendor.area by matching '
        'keywords in the existing address field against Bangladesh location data. '
        'The address field is left unchanged.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview the changes without saving them.',
        )
        parser.add_argument(
            '--show-unmatched',
            action='store_true',
            help='Print the most common addresses that did not match any city/area.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        show_unmatched = options['show_unmatched']

        area_candidates, district_candidates = build_candidates()

        customers = CustomerVendor.objects.exclude(address__isnull=True).exclude(address='')

        total = customers.count()
        matched_area = 0
        matched_city_only = 0
        unmatched = Counter()
        updated = 0

        for customer in customers.iterator():
            city, area = match_city_area(customer.address, area_candidates, district_candidates)

            if area:
                matched_area += 1
            elif city:
                matched_city_only += 1
            else:
                unmatched[customer.address.strip()] += 1

            if city != customer.city or area != customer.area:
                updated += 1
                if not dry_run:
                    customer.city = city
                    customer.area = area
                    customer.save(update_fields=['city', 'area'])

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry_run else ''}Processed {total} customers with an address."
        ))
        self.stdout.write(f"  Matched city + area: {matched_area}")
        self.stdout.write(f"  Matched city only:   {matched_city_only}")
        self.stdout.write(f"  No match:            {len(unmatched.values()) and sum(unmatched.values())}")
        self.stdout.write(f"  Rows {'that would be ' if dry_run else ''}updated: {updated}")

        if show_unmatched:
            self.stdout.write("\nMost common unmatched addresses:")
            for address, count in unmatched.most_common(30):
                self.stdout.write(f"  {count:3d}  {address}")

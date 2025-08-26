#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lekdedai.settings')

django.setup()

from lucky_spots.models import LuckyLocation, Region, Province, LocationCategory

print(f"Regions: {Region.objects.count()}")
print(f"Provinces: {Province.objects.count()}")
print(f"Categories: {LocationCategory.objects.count()}")
print(f"Locations: {LuckyLocation.objects.count()}")

if LuckyLocation.objects.exists():
    print("\nSample locations:")
    for loc in LuckyLocation.objects.all()[:5]:
        print(f"- {loc.name} ({loc.latitude}, {loc.longitude}) - {loc.province}")
else:
    print("No locations found!")
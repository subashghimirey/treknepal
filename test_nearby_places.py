import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'treknepal.settings')
django.setup()

from treks.utils import google_places_service

print("\n" + "="*80)
print("TESTING IF search_nearby_places IS BEING CALLED")
print("="*80 + "\n")

# Direct function call
print("Test 1: Direct function call")
places = google_places_service.search_nearby_places(27.7172, 85.3240, 'hospital')
print(f"Result: {len(places)} places found\n")

# Check if service is initialized
print("Test 2: Service initialization check")
print(f"API Key exists: {google_places_service.api_key is not None}")
print(f"API Key value: {google_places_service.api_key[:20]}..." if google_places_service.api_key else "None")
print()
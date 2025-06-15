import json
from django.core.management.base import BaseCommand
from treks.models import Trek

class Command(BaseCommand):
    help = 'Import trek data from JSON file'

    def handle(self, *args, **kwargs):
        with open('treks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        treks = []
        for item in data:
            trek = Trek(
                name=item.get("name"),
                district=item.get("district"),
                region=item.get("region"),
                difficulty=item.get("difficulty"),
                duration=item.get("duration"),
                best_seasons=item.get("best_seasons"),
                elevation_profile=item.get("elevation_profile"),
                description=item.get("description"),
                historical_significance=item.get("historical_significance"),
                itinerary=item.get("itinerary"),
                itinerary_points=item.get("itinerary_points"),
                cost_breakdown=item.get("cost_breakdown"),
                transportation=item.get("transportation"),
                nearby_attractions=item.get("nearby_attractions"),
                required_permits=item.get("required_permits"),
                recommended_gear=item.get("recommended_gear"),
                safety_info=item.get("safety_info"),
                photos=item.get("photos"),
                
            )
            treks.append(trek)

        Trek.objects.bulk_create(treks)
        self.stdout.write(self.style.SUCCESS(f"✅ Inserted {len(treks)} trek(s) into the database."))

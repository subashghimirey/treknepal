import json
from django.core.management.base import BaseCommand
from treks.models import EmergencyContactPoint

class Command(BaseCommand):
    help = 'Import emergency contact data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='emergency_contacts.json',
            help='Path to the JSON file containing emergency contacts'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing emergency contacts before importing'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"❌ File {file_path} not found.")
            )
            return
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f"❌ Invalid JSON in file {file_path}.")
            )
            return

        if options['clear']:
            deleted_count = EmergencyContactPoint.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f"🗑️  Deleted {deleted_count} existing emergency contacts.")
            )

        contacts = []
        for item in data:
            contact = EmergencyContactPoint(
                name=item.get("name"),
                type=item.get("type"), 
                email=item.get("email"),
                phone=item.get("phone"),
                latitude=item.get("latitude"),
                longitude=item.get("longitude")
            )
            contacts.append(contact)

        EmergencyContactPoint.objects.bulk_create(contacts)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully imported {len(contacts)} emergency contact(s)."
            )
        )
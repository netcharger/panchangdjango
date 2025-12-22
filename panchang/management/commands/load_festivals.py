"""
Management command to load festivals from JSON file into MySQL database
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from panchang.models import Festival


class Command(BaseCommand):
    help = 'Load festivals from festivals_panchangam_style.json into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='panchang_calculator/festivals_panchangam_style.json',
            help='Path to festivals JSON file',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing festivals before loading',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Try to find the file relative to project root or absolute path
        if not os.path.isabs(file_path):
            # Try relative to BASE_DIR (panchang_api directory)
            base_dir = settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            # If file path starts with 'panchang_calculator', go up one level to DAILYCALENDAR
            if file_path.startswith('panchang_calculator'):
                base_dir = base_dir.parent
            file_path = os.path.join(base_dir, file_path)
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        if options['clear']:
            count = Festival.objects.all().count()
            Festival.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing festivals'))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            festivals_data = json.load(f)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for idx, festival_data in enumerate(festivals_data, 1):
            # Skip entries without required festival_name field
            if 'festival_name' not in festival_data or not festival_data.get('festival_name'):
                self.stdout.write(
                    self.style.WARNING(f'Skipping entry {idx}: missing festival_name')
                )
                skipped_count += 1
                continue
            
            # Handle region field - it might be 'region' (singular) or 'regions' (plural)
            regions = festival_data.get('region', festival_data.get('regions', []))
            # Ensure regions is a list
            if not isinstance(regions, list):
                regions = [regions] if regions else []
            
            try:
                festival, created = Festival.objects.update_or_create(
                    festival_name=festival_data['festival_name'],
                    defaults={
                        'type': festival_data.get('type', ''),
                        'importance': festival_data.get('importance', 'Minor'),
                        'description': festival_data.get('description', ''),
                        'month': festival_data.get('month', ''),
                        'paksha': festival_data.get('paksha', ''),
                        'tithi': festival_data.get('tithi', ''),
                        'nakshatra': festival_data.get('nakshatra', ''),
                        'solar_event': festival_data.get('solar_event', ''),
                        'calculation_type': festival_data.get('calculation_type', 'lunar'),
                        'regions': regions,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing entry {idx} ({festival_data.get("festival_name", "unknown")}): {str(e)}')
                )
                skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded festivals: {created_count} created, {updated_count} updated, {skipped_count} skipped'
            )
        )


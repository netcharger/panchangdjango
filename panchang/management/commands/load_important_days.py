"""
Management command to load important days from JSON file into MySQL database
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from panchang.models import ImportantDay


class Command(BaseCommand):
    help = 'Load important days from important_days_india.json into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='panchang_calculator/important_days_india.json',
            help='Path to important days JSON file',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing important days before loading',
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
            count = ImportantDay.objects.all().count()
            ImportantDay.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing important days'))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            days_data = json.load(f)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        sequence_id = 1  # Start from 1 for first record
        
        for day_entry in days_data:
            date_str = day_entry.get('date', '')
            events = day_entry.get('events', [])
            
            if not date_str:
                self.stdout.write(
                    self.style.WARNING(f'Skipping entry: missing date')
                )
                skipped_count += 1
                continue
            
            for event in events:
                # Skip entries without required day_name field
                if 'day_name' not in event or not event.get('day_name'):
                    self.stdout.write(
                        self.style.WARNING(f'Skipping event on {date_str}: missing day_name')
                    )
                    skipped_count += 1
                    continue
                
                # Get holiday scope regions if available
                holiday_scope = event.get('holiday_scope', {})
                regions = holiday_scope.get('states', event.get('region', []))
                # Ensure regions is a list
                if not isinstance(regions, list):
                    regions = [regions] if regions else []
                
                try:
                    day, created = ImportantDay.objects.update_or_create(
                        date=date_str,
                        day_name=event['day_name'],
                        defaults={
                            'sequence_id': sequence_id,  # Assign sequential ID
                            'type_of': event.get('type_of', ''),
                            'importance': event.get('importance', 'Minor'),
                            'description': event.get('description', ''),
                            'is_holiday': event.get('is_holiday', ''),
                            'regions': regions,
                            'calendar_type': event.get('calendar_type', 'gregorian'),
                        }
                    )
                    
                    # Update sequence_id even if record already exists
                    if not created and day.sequence_id != sequence_id:
                        day.sequence_id = sequence_id
                        day.save(update_fields=['sequence_id'])
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    
                    sequence_id += 1  # Increment for next record
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing event on {date_str} ({event.get("day_name", "unknown")}): {str(e)}')
                    )
                    skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded important days: {created_count} created, {updated_count} updated, {skipped_count} skipped'
            )
        )


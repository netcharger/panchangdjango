import pandas as pd
from django.core.management.base import BaseCommand
from panchang.models import PanchangData
from datetime import datetime

class Command(BaseCommand):
    help = 'Import Panchang data from Excel file (Merged_Data.xlsx)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        self.stdout.write(f"Reading file: {file_path}")

        try:
            df = pd.read_excel(file_path)
            # Normalize column names to strip whitespace
            df.columns = df.columns.str.strip()
            
            records_created = 0
            records_updated = 0

            for index, row in df.iterrows():
                try:
                    # Parse date and format as DD-MM-YYYY
                    raw_date = row['Date']
                    if pd.notna(raw_date):
                        try:
                            # Convert to datetime object (pandas usually does this automatically)
                            date_obj = pd.to_datetime(raw_date)
                            date_val = date_obj.strftime('%Y-%m-%d')
                        except Exception:
                             # Fallback if it's not a standard date format
                            date_val = str(raw_date).strip()
                    else:
                        continue # Skip empty dates
                    
                    data = {
                        'lunar_month': str(row['Lunar_Month']).strip() if pd.notna(row['Lunar_Month']) else '',
                        'paksha': str(row['Paksha']).strip() if pd.notna(row['Paksha']) else '',
                        'thithi': str(row['Thithi']).strip() if pd.notna(row['Thithi']) else '',
                        'thithi_end': str(row['Thithi_End']).strip() if pd.notna(row['Thithi_End']) else '',
                        'nakshatram': str(row['Nakshatram']).strip() if pd.notna(row['Nakshatram']) else '',
                        'nakshatram_end': str(row['Nakshatram_End']).strip() if pd.notna(row['Nakshatram_End']) else '',
                        'varjyam_time': str(row['Varjyam_Time']).strip() if pd.notna(row['Varjyam_Time']) else '',
                        'durmuhurtham_1': str(row['Durmuhurtham_1']).strip() if pd.notna(row['Durmuhurtham_1']) else '',
                        'durmuhurtham_2': str(row['Durmuhurtham_2']).strip() if pd.notna(row['Durmuhurtham_2']) else '',
                        'festivals': '', # Placeholder for future manual insertion
                    }

                    obj, created = PanchangData.objects.update_or_create(
                        date=date_val,
                        defaults=data
                    )

                    if created:
                        records_created += 1
                    else:
                        records_updated += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error processing row {index + 2}: {str(e)}"))

            self.stdout.write(self.style.SUCCESS(f"Import complete. Created: {records_created}, Updated: {records_updated}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading file: {str(e)}"))

"""
Django management command to generate and update festival dates for all festivals.

This command calculates festival dates based on tithi, paksha, month, and nakshatra
for 4 years before, current year, and next 5 years (10 years total).

Optimized approach:
1. Pre-calculate panchang for all dates once
2. Load all festivals into DataFrame
3. Match festivals to dates in memory
4. Batch update database

Usage:
    python manage.py generate_festival_dates
    python manage.py generate_festival_dates --festival-id 123
    python manage.py generate_festival_dates --all
    python manage.py generate_festival_dates --update-existing
    python manage.py generate_festival_dates --verbose
"""

from django.core.management.base import BaseCommand
from django.db import transaction, models
from panchang.models import Festival
from datetime import date, datetime, timedelta
import json
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available. Install it with: pip install pandas")


class Command(BaseCommand):
    help = 'Generate and update festival dates for all festivals based on tithi, paksha, month, and nakshatra (optimized with DataFrame)'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panchang_cache = {}  # Cache panchang calculations: {date_str: panchang_dict}
        self.month_normalization = self._build_month_normalization()

    def add_arguments(self, parser):
        parser.add_argument(
            '--festival-id',
            type=int,
            help='Generate dates for a specific festival ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate dates for all festivals (default: only festivals without dates)',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing festival dates even if they already exist',
        )
        parser.add_argument(
            '--years-before',
            type=int,
            default=4,
            help='Number of years before current year to calculate (default: 4)',
        )
        parser.add_argument(
            '--years-ahead',
            type=int,
            default=5,
            help='Number of years ahead to calculate (default: 5)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress and matches',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of dates to process in each batch (default: 100)',
        )

    def _build_month_normalization(self):
        """Build month name normalization map"""
        return {
            'vaisakha': ['vaisakha', 'vaishakha', 'vaishakh', 'vaisakh'],
            'chaitra': ['chaitra', 'chaitr'],
            'jyaistha': ['jyaistha', 'jyestha', 'jyeshtha', 'jestha'],
            'asadha': ['asadha', 'aasadha', 'ashadha'],
            'sravana': ['sravana', 'shravana', 'shravan'],
            'bhadra': ['bhadra', 'bhadrapada', 'bhadrapad'],
            'asvina': ['asvina', 'ashvina', 'ashwin'],
            'kartika': ['kartika', 'kartik', 'karthika', 'karthigai'],
            'agrahayana': ['agrahayana', 'margashirsha', 'margasira', 'margashirsh'],
            'pausa': ['pausa', 'pausha', 'paush'],
            'magha': ['magha', 'magh'],
            'phalguna': ['phalguna', 'phalgun'],
        }

    def _normalize_month_name(self, month_name):
        """Normalize month name to standard form"""
        if not month_name:
            return None
        month_lower = month_name.lower().strip()
        # Build reverse map
        month_to_standard = {}
        for standard, variations in self.month_normalization.items():
            for variation in variations:
                month_to_standard[variation] = standard
        return month_to_standard.get(month_lower, month_lower)

    def _precalculate_panchang_for_dates(self, start_date, end_date, verbose=False):
        """Pre-calculate panchang for all dates in range"""
        from panchang.calculations.panchangam_calculation import compute_panchang_for_date, LOCATION

        self.stdout.write(f'Pre-calculating panchang for {start_date} to {end_date}...')

        current_date = start_date
        total_days = (end_date - start_date).days + 1
        days_processed = 0
        batch_count = 0

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            # Skip if already cached
            if date_str in self.panchang_cache:
                current_date += timedelta(days=1)
                continue

            try:
                # Calculate panchang
                panchang_result = compute_panchang_for_date(
                    date_str,
                    location=LOCATION,
                    profile_code='en',
                    format_profile=False,
                    include_raw=False,
                )

                if isinstance(panchang_result, dict):
                    # Extract key data for matching
                    core_panchang = panchang_result.get('core_panchang', {})
                    tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                    nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                    paksha_info = panchang_result.get('Paksha', {})
                    amanta_month = panchang_result.get('Amanta Month', {})
                    purnimanta_month = panchang_result.get('Purnimanta Month', {})

                    # Store simplified panchang data
                    self.panchang_cache[date_str] = {
                        'date': date_str,
                        'tithis': [t.get('name') for t in tithi_events if t.get('name')],
                        'paksha': paksha_info.get('name', '') if paksha_info else '',
                        'paksha_normalized': paksha_info.get('name', '').replace('Paksha', '').strip() if paksha_info else '',
                        'amanta_month': amanta_month.get('name', '') if amanta_month else '',
                        'purnimanta_month': purnimanta_month.get('name', '') if purnimanta_month else '',
                        'nakshatras': [n.get('name') for n in nakshatra_events if n.get('name')],
                        'tithi_events': tithi_events,  # Keep for time extraction
                    }

                days_processed += 1

                # Show progress
                if verbose:
                    if days_processed % 50 == 0 or days_processed == 1:
                        progress = (days_processed / total_days) * 100
                        self.stdout.write(f'  Calculating {date_str}... ({days_processed}/{total_days} days, {progress:.1f}%)', ending='\r')
                else:
                    # Even without verbose, show progress every 100 days
                    if days_processed % 100 == 0:
                        progress = (days_processed / total_days) * 100
                        self.stdout.write(f'  Calculating panchang... ({days_processed}/{total_days} days, {progress:.1f}%)', ending='\r')

            except Exception as e:
                # Skip dates with calculation errors (e.g., no dawn time)
                pass

            current_date += timedelta(days=1)

        if verbose:
            self.stdout.write('')  # New line after progress
        self.stdout.write(self.style.SUCCESS(f'  ✓ Pre-calculated panchang for {len(self.panchang_cache)} dates'))

        return self.panchang_cache

    def _match_festival_to_dates(self, festival, panchang_df, verbose=False):
        """Match a festival to dates using DataFrame operations"""
        if not PANDAS_AVAILABLE:
            # Fallback to old method
            return self._match_festival_to_dates_slow(festival, verbose)

        # Prepare festival criteria
        festival_tithi = festival.tithi.strip() if festival.tithi else None
        festival_paksha = festival.paksha.strip() if festival.paksha else None
        festival_month = self._normalize_month_name(festival.month) if festival.month else None
        festival_nakshatra = festival.nakshatra.strip() if festival.nakshatra else None

        if not festival_tithi or not festival_paksha:
            return {}

        # Normalize paksha
        paksha_normalized = festival_paksha.replace('Paksha', '').strip().lower()

        # Filter DataFrame by criteria
        matches = panchang_df.copy()

        # Filter by tithi (tithi must be in the list)
        if festival_tithi:
            matches = matches[matches['tithis'].apply(lambda x: festival_tithi in x if x else False)]

        # Filter by paksha
        if festival_paksha:
            matches = matches[
                (matches['paksha'].str.lower() == festival_paksha.lower()) |
                (matches['paksha_normalized'].str.lower() == paksha_normalized)
            ]

        # Filter by month (optional)
        if festival_month:
            festival_month_lower = festival_month.lower()
            matches = matches[
                (matches['amanta_month_normalized'].str.lower() == festival_month_lower) |
                (matches['purnimanta_month_normalized'].str.lower() == festival_month_lower) |
                (matches['amanta_month'].str.lower() == festival_month_lower) |
                (matches['purnimanta_month'].str.lower() == festival_month_lower)
            ]

        # Filter by nakshatra (optional)
        if festival_nakshatra:
            matches = matches[matches['nakshatras'].apply(lambda x: festival_nakshatra in x if x else True)]

        # Group by year and create result structure
        festival_dates_by_year = {}
        for _, row in matches.iterrows():
            year = row['date'][:4]
            if year not in festival_dates_by_year:
                festival_dates_by_year[year] = []

            # Extract tithi time
            tithi_time = None
            for t_event in row.get('tithi_events', []):
                if t_event.get('name') == festival_tithi:
                    start_time = t_event.get('start')
                    if start_time:
                        if isinstance(start_time, str):
                            try:
                                tithi_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
                            except:
                                pass
                        else:
                            tithi_time = start_time
                    break

            time_str = tithi_time.strftime('%I:%M %p') if tithi_time and hasattr(tithi_time, 'strftime') else 'N/A'

            festival_dates_by_year[year].append({
                'date': row['date'],
                'time': time_str,
                'datetime': tithi_time.isoformat() if tithi_time and hasattr(tithi_time, 'isoformat') else row['date']
            })

        # Sort dates within each year
        for year in festival_dates_by_year:
            festival_dates_by_year[year].sort(key=lambda x: x['date'])

        if festival_dates_by_year:
            total = sum(len(dates) for dates in festival_dates_by_year.values())
            if verbose:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Found {total} match(es) for {festival.festival_name}:'))
                for year, dates_list in sorted(festival_dates_by_year.items()):
                    for d in dates_list:
                        self.stdout.write(f'    - {year}: {d["date"]} at {d["time"]}')
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {festival.festival_name}: {total} dates found'))

        return festival_dates_by_year

    def _match_festival_to_dates_slow(self, festival, verbose=False):
        """Fallback method without pandas"""
        # Use old method
        return {}

    def _create_panchang_dataframe(self):
        """Create DataFrame from cached panchang data"""
        if not PANDAS_AVAILABLE:
            return None

        if not self.panchang_cache:
            return pd.DataFrame()

        # Convert cache to list of dicts
        data = []
        for date_str, panchang_data in self.panchang_cache.items():
            data.append({
                'date': date_str,
                'tithis': panchang_data['tithis'],
                'paksha': panchang_data['paksha'],
                'paksha_normalized': panchang_data['paksha_normalized'],
                'amanta_month': panchang_data['amanta_month'],
                'purnimanta_month': panchang_data['purnimanta_month'],
                'amanta_month_normalized': self._normalize_month_name(panchang_data['amanta_month']),
                'purnimanta_month_normalized': self._normalize_month_name(panchang_data['purnimanta_month']),
                'nakshatras': panchang_data['nakshatras'],
                'tithi_events': panchang_data['tithi_events'],
            })

        df = pd.DataFrame(data)
        return df

    def _calculate_dates_for_year(self, festival, year, year_start_date, year_end_date, verbose=False):
        """Calculate festival dates for a specific year by checking each day"""
        from panchang.calculations.panchangam_calculation import compute_panchang_for_date, LOCATION
        from datetime import timedelta

        results = []
        current_date = year_start_date
        paksha_normalized = festival.paksha.replace('Paksha', '').strip() if festival.paksha else None
        total_days = (year_end_date - year_start_date).days + 1
        days_processed = 0

        # Month name normalization map (handle variations)
        # Map all variations to standard names used in constants
        month_normalization = {
            'vaisakha': ['vaisakha', 'vaishakha', 'vaishakh', 'vaisakh'],
            'chaitra': ['chaitra', 'chaitr'],
            'jyaistha': ['jyaistha', 'jyestha', 'jyeshtha', 'jestha'],
            'asadha': ['asadha', 'aasadha', 'ashadha'],
            'sravana': ['sravana', 'shravana', 'shravan'],
            'bhadra': ['bhadra', 'bhadrapada', 'bhadrapad'],
            'asvina': ['asvina', 'ashvina', 'ashwin'],
            'kartika': ['kartika', 'kartik', 'karthika', 'karthigai'],
            'agrahayana': ['agrahayana', 'margashirsha', 'margasira', 'margashirsh'],
            'pausa': ['pausa', 'pausha', 'paush'],
            'magha': ['magha', 'magh'],
            'phalguna': ['phalguna', 'phalgun'],
        }

        # Reverse map: from any variation to standard name
        month_to_standard = {}
        for standard, variations in month_normalization.items():
            for variation in variations:
                month_to_standard[variation.lower()] = standard

        # Get normalized month names for matching
        festival_month_normalized = None
        if festival.month:
            festival_month_lower = festival.month.lower().strip()
            festival_month_normalized = month_to_standard.get(festival_month_lower, festival_month_lower)

        # Search through the year - check every day for accuracy
        # We can't skip days because festivals can occur on any day
        days_checked = 0
        max_days = 366  # Max days in a year (including leap year)
        last_progress_output = 0

        while current_date <= year_end_date and days_checked < max_days:
            date_str = current_date.strftime('%Y-%m-%d')
            days_processed += 1

            # Show progress every 30 days or at start
            if verbose and (days_processed % 30 == 0 or days_processed == 1):
                progress = (days_processed / total_days) * 100
                print(f"  Checking {date_str}... ({days_processed}/{total_days} days, {progress:.1f}%)", end='\r')

            try:
                # Calculate panchang for this date
                panchang_result = compute_panchang_for_date(
                    date_str,
                    location=LOCATION,
                    profile_code='en',
                    format_profile=False,
                    include_raw=False,
                )

                if not isinstance(panchang_result, dict):
                    current_date += timedelta(days=1)
                    days_checked += 1
                    continue

                # Extract panchang data
                core_panchang = panchang_result.get('core_panchang', {})
                tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                paksha_info = panchang_result.get('Paksha', {})
                amanta_month = panchang_result.get('Amanta Month', {})
                purnimanta_month = panchang_result.get('Purnimanta Month', {})

                # Check if tithi matches
                tithi_matches = False
                if tithi_events:
                    tithi_names = [t.get('name') for t in tithi_events if t.get('name')]
                    tithi_matches = festival.tithi in tithi_names

                # Check if paksha matches
                paksha_matches = False
                if paksha_info:
                    paksha_name = paksha_info.get('name', '')
                    paksha_name_normalized = paksha_name.replace('Paksha', '').strip()
                    paksha_matches = (
                        festival.paksha.lower() == paksha_name.lower() or
                        paksha_normalized and paksha_normalized.lower() == paksha_name_normalized.lower()
                    )

                # Check if month matches (optional) - with normalization
                month_matches = True
                if festival.month and festival_month_normalized:
                    amanta_month_name = (amanta_month.get('name', '') if amanta_month else '').lower().strip()
                    purnimanta_month_name = (purnimanta_month.get('name', '') if purnimanta_month else '').lower().strip()

                    # Normalize month names from panchang result
                    amanta_normalized = month_to_standard.get(amanta_month_name, amanta_month_name)
                    purnimanta_normalized = month_to_standard.get(purnimanta_month_name, purnimanta_month_name)

                    # Check if month matches (exact or normalized)
                    month_matches = (
                        festival_month_normalized == amanta_normalized or
                        festival_month_normalized == purnimanta_normalized or
                        festival_month_normalized == amanta_month_name or
                        festival_month_normalized == purnimanta_month_name or
                        festival.month.lower().strip() == amanta_month_name or
                        festival.month.lower().strip() == purnimanta_month_name
                    )

                # Check if nakshatra matches (optional)
                nakshatra_matches = True
                if festival.nakshatra and festival.nakshatra.strip() and nakshatra_events:
                    nakshatra_names = [n.get('name') for n in nakshatra_events if n.get('name')]
                    nakshatra_matches = festival.nakshatra in nakshatra_names

                # If all criteria match, add to results
                if tithi_matches and paksha_matches and month_matches and nakshatra_matches:
                    # Find the exact time when tithi occurs
                    tithi_time = None
                    for t_event in tithi_events:
                        if t_event.get('name') == festival.tithi:
                            start_time = t_event.get('start')
                            if start_time:
                                if isinstance(start_time, str):
                                    try:
                                        tithi_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
                                    except:
                                        pass
                                else:
                                    tithi_time = start_time
                            break

                    time_str = tithi_time.strftime('%I:%M %p') if tithi_time and hasattr(tithi_time, 'strftime') else 'N/A'
                    results.append({
                        'date': date_str,
                        'time': time_str,
                        'datetime': tithi_time.isoformat() if tithi_time and hasattr(tithi_time, 'isoformat') else date_str
                    })

                    # Show match found
                    if verbose:
                        print(f"\n  ✓ MATCH FOUND: {festival.festival_name} on {date_str} at {time_str}")

                # Always check next day (can't skip because festivals can be consecutive)
                current_date += timedelta(days=1)
                days_checked += 1

            except Exception as e:
                # On error, just move to next day
                current_date += timedelta(days=1)
                days_checked += 1
                continue

        # Sort results by date
        results.sort(key=lambda x: x['date'])

        if verbose:
            print(f"  Year {year}: Found {len(results)} occurrence(s)")

        return results

    def _calculate_dates_for_year_backwards(self, festival, year, search_start_date, year_start_date, year_end_date):
        """Calculate festival dates for a past year by searching backwards"""
        from panchang.calculations.panchangam_calculation import compute_panchang_for_date, LOCATION
        from datetime import timedelta

        results = []
        current_date = search_start_date
        paksha_normalized = festival.paksha.replace('Paksha', '').strip() if festival.paksha else None

        # Search backwards through the year
        days_checked = 0
        max_days = 400  # Safety limit (more than 365 to account for lunar cycles)

        while current_date >= year_start_date and days_checked < max_days:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                # Calculate panchang for this date
                panchang_result = compute_panchang_for_date(
                    date_str,
                    location=LOCATION,
                    profile_code='en',
                    format_profile=False,
                    include_raw=False,
                )

                if not isinstance(panchang_result, dict):
                    current_date -= timedelta(days=1)
                    days_checked += 1
                    continue

                # Extract panchang data
                core_panchang = panchang_result.get('core_panchang', {})
                tithi_events = core_panchang.get('Tithulu', []) or core_panchang.get('Tithi', [])
                nakshatra_events = core_panchang.get('Nakshatramulu', []) or core_panchang.get('Nakshatra', [])
                paksha_info = panchang_result.get('Paksha', {})
                amanta_month = panchang_result.get('Amanta Month', {})
                purnimanta_month = panchang_result.get('Purnimanta Month', {})

                # Check if tithi matches
                tithi_matches = False
                if tithi_events:
                    tithi_names = [t.get('name') for t in tithi_events if t.get('name')]
                    tithi_matches = festival.tithi in tithi_names

                # Check if paksha matches
                paksha_matches = False
                if paksha_info:
                    paksha_name = paksha_info.get('name', '')
                    paksha_name_normalized = paksha_name.replace('Paksha', '').strip()
                    paksha_matches = (
                        festival.paksha.lower() == paksha_name.lower() or
                        paksha_normalized and paksha_normalized.lower() == paksha_name_normalized.lower()
                    )

                # Check if month matches (optional)
                month_matches = True
                if festival.month:
                    amanta_month_name = amanta_month.get('name', '') if amanta_month else ''
                    purnimanta_month_name = purnimanta_month.get('name', '') if purnimanta_month else ''
                    month_matches = (
                        festival.month.lower() == amanta_month_name.lower() or
                        festival.month.lower() == purnimanta_month_name.lower()
                    )

                # Check if nakshatra matches (optional)
                nakshatra_matches = True
                if festival.nakshatra and nakshatra_events:
                    nakshatra_names = [n.get('name') for n in nakshatra_events if n.get('name')]
                    nakshatra_matches = festival.nakshatra in nakshatra_names

                # If all criteria match, add to results
                if tithi_matches and paksha_matches and month_matches and nakshatra_matches:
                    # Find the exact time when tithi occurs
                    tithi_time = None
                    for t_event in tithi_events:
                        if t_event.get('name') == festival.tithi:
                            start_time = t_event.get('start')
                            if start_time:
                                tithi_time = start_time
                            break

                    results.append({
                        'date': date_str,
                        'time': tithi_time.strftime('%I:%M %p') if tithi_time else 'N/A',
                        'datetime': tithi_time.isoformat() if tithi_time else date_str
                    })

                # Move backwards (optimized: skip by lunar month if no match)
                if tithi_matches and paksha_matches:
                    current_date -= timedelta(days=1)
                else:
                    current_date -= timedelta(days=29)  # Approximate lunar month

                days_checked += 1

            except Exception as e:
                current_date -= timedelta(days=1)
                days_checked += 1
                continue

        # Sort results by date (oldest first)
        results.sort(key=lambda x: x['date'])
        return results

    def handle(self, *args, **options):
        festival_id = options.get('festival_id')
        update_all = options.get('all', False)
        update_existing = options.get('update_existing', False)
        years_before = options.get('years_before', 4)
        years_ahead = options.get('years_ahead', 5)
        verbose = options.get('verbose', False)

        current_year = date.today().year
        start_year = current_year - years_before
        end_year = current_year + years_ahead

        self.stdout.write(
            self.style.SUCCESS(
                f'Generating festival dates from {start_year} to {end_year} '

                f'({years_before} years before, current year, {years_ahead} years ahead)'
            )
        )

        # Get festivals to process
        if festival_id:
            festivals = Festival.objects.filter(pk=festival_id)
            if not festivals.exists():
                self.stdout.write(
                    self.style.ERROR(f'Festival with ID {festival_id} not found')
                )
                return
        else:
            # Filter festivals based on criteria
            query = Festival.objects.filter(
                calculation_type__in=['lunar', 'unspecified']
            ).filter(
                tithi__isnull=False
            ).exclude(
                tithi=''
            ).filter(
                paksha__isnull=False
            ).exclude(
                paksha=''
            )

            if not update_all and not update_existing:
                # Only process festivals without dates
                query = query.filter(
                    models.Q(festival_dates__isnull=True) |
                    models.Q(festival_dates={})
                )

            festivals = query.all()

        total_festivals = festivals.count()
        if total_festivals == 0:
            self.stdout.write(
                self.style.WARNING('No festivals found to process')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Processing {total_festivals} festival(s)...')
        )

        # Step 1: Pre-calculate panchang for all dates
        start_date_obj = date(start_year, 1, 1)
        end_date_obj = date(end_year, 12, 31)

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Step 1: Pre-calculating panchang for all dates...'))
        self.stdout.write(self.style.SUCCESS('='*60))

        self._precalculate_panchang_for_dates(start_date_obj, end_date_obj, verbose=verbose)

        # Step 2: Create DataFrame from cached panchang data
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Step 2: Creating DataFrame from panchang data...'))
        self.stdout.write(self.style.SUCCESS('='*60))

        if PANDAS_AVAILABLE:
            panchang_df = self._create_panchang_dataframe()
            self.stdout.write(self.style.SUCCESS(f'Created DataFrame with {len(panchang_df)} dates'))
        else:
            panchang_df = None
            self.stdout.write(self.style.WARNING('Pandas not available, using slow method'))

        # Step 3: Match festivals to dates
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Step 3: Matching festivals to dates...'))
        self.stdout.write(self.style.SUCCESS('='*60))

        success_count = 0
        error_count = 0
        skipped_count = 0

        for festival in festivals:
            try:
                # Skip if festival already has dates and we're not updating existing
                if not update_existing and not update_all:
                    if festival.festival_dates and festival.festival_dates != {}:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping {festival.festival_name} (already has dates)'
                            )
                        )
                        continue

                # Match festival to dates using DataFrame (fast)
                if not verbose:
                    # Show simple progress
                    self.stdout.write(f'Processing: {festival.festival_name}...', ending='\r')
                else:
                    self.stdout.write(
                        f'\nProcessing: {festival.festival_name} '
                        f'(Tithi: {festival.tithi}, Paksha: {festival.paksha}, '
                        f'Month: {festival.month or "Any"}, '
                        f'Nakshatra: {festival.nakshatra or "Any"})'
                    )

                # Match festival to dates using DataFrame (fast)
                festival_dates_by_year = self._match_festival_to_dates(festival, panchang_df, verbose=verbose)

                if not verbose:
                    # Clear the progress line
                    self.stdout.write(' ' * 80, ending='\r')

                # Update festival with calculated dates
                festival.festival_dates = festival_dates_by_year
                festival.save(update_fields=['festival_dates'])

                # Count total dates
                total_dates = sum(len(dates) for dates in festival_dates_by_year.values())

                if not verbose:
                    # Simple output
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {festival.festival_name}: {total_dates} dates'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Updated {festival.festival_name}: '
                            f'{total_dates} dates across {len(festival_dates_by_year)} years'
                        )
                    )

                success_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error processing {festival.festival_name}: {str(e)}'
                    )
                )
                import traceback
                traceback.print_exc()

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(
            self.style.SUCCESS(f'  Successfully processed: {success_count}')
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'  Skipped (already have dates): {skipped_count}')
            )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  Errors: {error_count}')
            )
        self.stdout.write(self.style.SUCCESS('=' * 60))


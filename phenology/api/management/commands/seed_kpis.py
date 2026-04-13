"""
Seed dummy KPI data for all blocks across multiple periods.

Usage:
    python manage.py seed_kpis
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Block, KPI


PERIODS = ['2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4', '2025-Q1', '2025-Q2']

# Per-period dummy values [fungicide%, fuel%, co2_kg, yield%]
PERIOD_DATA = {
    '2024-Q1': (12.0,  8.0,  45.0,  -2.0),
    '2024-Q2': (18.5, 11.0,  62.0,  -1.5),
    '2024-Q3': (22.0, 14.5,  80.0,   0.5),
    '2024-Q4': (15.0, 10.0,  55.0,  -3.0),
    '2025-Q1': (25.0, 16.0,  95.0,   1.0),
    '2025-Q2': (30.0, 20.0, 120.0,   2.5),
}


class Command(BaseCommand):
    help = 'Seed dummy KPI data for all blocks'

    def handle(self, *args, **kwargs):
        blocks = Block.objects.all()
        if not blocks.exists():
            self.stdout.write(self.style.WARNING('No blocks found. Create blocks first.'))
            return

        user = User.objects.first()
        created = 0

        for block in blocks:
            for period, (fung, fuel, co2, yld) in PERIOD_DATA.items():
                # Slight variation per block so charts look interesting
                offset = hash(str(block.id)) % 5
                _, was_created = KPI.objects.get_or_create(
                    block=block,
                    period=period,
                    defaults={
                        'fungicide_reduction': round(fung + offset,   2),
                        'fuel_reduction':      round(fuel + offset,   2),
                        'co2_reduction':       round(co2  + offset*2, 2),
                        'yield_reduction':     round(yld  + offset*0.5 - 1, 2),
                        'created_by': user,
                        'updated_by': user,
                    }
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} KPI records across {blocks.count()} blocks.'))

from django.core.management.base import BaseCommand
from ...utils import archive_old_appointments

class Command(BaseCommand):
    help = 'Archives appointments older than the specified number of days'

    def add_arguments(self, parser):
        parser.add_argument('days', type=int, default=365, nargs='?',
                            help='Number of days old an appointment should be before archiving')

    def handle(self, *args, **options):
        days = options['days']
        archived_count = archive_old_appointments(days)
        self.stdout.write(self.style.SUCCESS(f'Successfully archived {archived_count} appointments older than {days} days.'))
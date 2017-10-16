from django.core.management.base import BaseCommand, CommandError
from engine.engines import update_model

class Command(BaseCommand):
    """
    Runs engine model optimization

    Usage:
        python manage.py update_model [--eta] [--M]

    Example:
        python manage.py update_model --eta 0.0 --M 20.0
    """

    help = 'Updates model'

    def add_arguments(self, parser):
        parser.add_argument('--eta', type=float, default=0.0)
        parser.add_argument('--M', type=float, default=0.0)

    def handle(self, *args, **options):
        self.stdout.write(
            'Starting model update with parameters eta={} and M={}'.format(
                options['eta'],options['M']
            )
        )

        update_model(eta=options['eta'], M=options['M'])

        self.stdout.write(self.style.SUCCESS('Successfully ran model update'))

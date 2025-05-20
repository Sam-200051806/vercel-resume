from django.contrib.staticfiles.management.commands import collectstatic
from django.db import connections


class Command(collectstatic.Command):
    """
    A version of collectstatic that doesn't require database access.
    This is useful for environments like Vercel where we don't have a database.
    """

    def handle(self, **options):
        # Close any existing database connections
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()

        # Set the --skip-checks option to avoid database checks
        options['skip_checks'] = True

        # Call the parent handle method
        return super().handle(**options)

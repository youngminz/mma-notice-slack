from django.core.management.base import BaseCommand

from ...scraper import scrap_work_mma


class Command(BaseCommand):
    def handle(self, *args, **options):
        scrap_work_mma()

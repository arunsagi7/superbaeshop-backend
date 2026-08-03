import os
import sys

import django

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
django.setup()

from django.core.management.base import BaseCommand
from product_management.models import Products
from categories.models import HomepageSectionProduct

class Command(BaseCommand):
    help = 'Populate product foreign key for HomepageSectionProduct based on matching title'

    def handle(self, *args, **options):
        updated = 0
        not_found = []
        for hsp in HomepageSectionProduct.objects.all():
            if hsp.product_id:
                continue  # already linked
            title = hsp.title.strip()
            try:
                product = Products.objects.get(title__iexact=title)
                hsp.product = product
                hsp.save(update_fields=['product'])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Linked '{title}' to product ID {product.id}"))
            except Products.DoesNotExist:
                not_found.append(title)
                self.stdout.write(self.style.WARNING(f"No product found for title '{title}'"))
        self.stdout.write(self.style.SUCCESS(f"Finished. Updated {updated} records."))
        if not_found:
            self.stdout.write(self.style.ERROR(f"Titles not matched: {', '.join(not_found)}"))

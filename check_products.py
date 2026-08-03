import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

from product_management.models import Products
from categories.models import HomepageSection
from product_management.models import ProductAvailableCountries

sys.stdout.reconfigure(encoding='utf-8')

print("=== PRODUCTS ===")
print(f"Total products: {Products.objects.count()}")
for p in Products.objects.all():
    print(f"ID={p.id}, SKU={p.sku}, Title={p.title}, Status={p.status}, Active={p.is_active}")

print("\n=== PRODUCT AVAILABLE COUNTRIES ===")
for pc in ProductAvailableCountries.objects.all():
    print(f"ID={pc.id}, Product={pc.product.title}, Country={pc.country}, Original={pc.original_price}, Selling={pc.selling_price}")

print("\n=== HOMEPAGE SECTIONS ===")
print(f"Total sections: {HomepageSection.objects.count()}")
for s in HomepageSection.objects.all():
    print(f"ID={s.id}, Type={s.section_type}, Title={s.title}, Active={s.is_active}")

print("\n=== CATEGORIES ===")
from categories.models import Categories, SuperCategories
for sc in SuperCategories.objects.all():
    print(f"SuperCategory: ID={sc.id}, Title={sc.title}")
for c in Categories.objects.all():
    print(f"Category: ID={c.id}, Title={c.title}, SuperCategory={c.super_category.title}")

from categories.models import Countries
print("\n=== COUNTRIES ===")
for c in Countries.objects.all():
    print(f"ID={c.id}, Title={c.title}, Code={c.code}, Code2={c.code2}")
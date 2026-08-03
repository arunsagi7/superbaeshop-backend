import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries
from categories.models import Categories, Countries
from django.utils.text import slugify
import random

# Get or create categories
cat_stickers, _ = Categories.objects.get_or_create(title="Stickers", defaults={"is_active": True})
cat_notebooks, _ = Categories.objects.get_or_create(title="Notebooks", defaults={"is_active": True})
cat_planners, _ = Categories.objects.get_or_create(title="Planners", defaults={"is_active": True})
cat_stationery, _ = Categories.objects.get_or_create(title="Stationery", defaults={"is_active": True})

# Get countries
countries = {c.code2: c for c in Countries.objects.all()}

# Helper function to create product with country pricing
def create_product_with_country(title, category, prices_dict, stock=100, product_id=None):
    slug = slugify(title)
    product_data = {
        'sku': f"SKU-{random.randint(1000, 9999)}",
        'title': title,
        'slug': slug,
        'category': category,
        'support_number': "9999999999",
        'stock_qty': stock,
        'weight': random.uniform(0.1, 2.0),
        'is_active': True,
        'status': 5
    }
    
    if product_id:
        # Force the ID by using raw SQL or by updating after creation
        product = Products.objects.create(**product_data)
        # Update the ID if needed (SQLite allows this)
        if product.id != product_id:
            # For SQLite, we can update the id
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("UPDATE tbl_products SET id = %s WHERE id = %s" % (product_id, product.id))
            product.id = product_id
    else:
        product = Products.objects.create(**product_data)
    
    for country_code2, price_data in prices_dict.items():
        if country_code2 in countries:
            country = countries[country_code2]
            ProductAvailableCountries.objects.create(
                product=product,
                country=country,
                original_price=price_data.get('original_price', price_data['price'] * 1.2),
                selling_price=price_data['price']
            )
    return product

print("Adding missing products (IDs 202, 207)...")

# Create the missing products that frontend is trying to use
missing_products = [
    (202, 'Test Product 202', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 23.99}),
    (207, 'Test Product 207', cat_notebooks, {'in': 12.99, 'au': 18.99, 'sg': 16.99, 'ar': 15.99}),
]

for product_id, title, category, prices in missing_products:
    # Check if product already exists
    if Products.objects.filter(id=product_id).exists():
        print(f"  Product ID {product_id} already exists, skipping...")
        continue
    
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()}, product_id=product_id)
    print(f"  Created: ID={p.id}, Title={p.title}")

print("\n=== Adding country pricing for existing products ===")

# Add country pricing for all existing products
for product in Products.objects.all():
    if not product.product_country.exists():
        # Add pricing for India, Australia, Singapore, Argentina
        for country_code2 in ['in', 'au', 'sg', 'ar']:
            if country_code2 in countries:
                country = countries[country_code2]
                base_price = random.uniform(10, 50)
                ProductAvailableCountries.objects.create(
                    product=product,
                    country=country,
                    original_price=base_price * 1.2,
                    selling_price=base_price
                )
        print(f"  Added pricing for: {product.title}")

print("\n=== VERIFICATION ===")
print(f"Total products now: {Products.objects.count()}")
for pid in [202, 207]:
    try:
        p = Products.objects.get(id=pid)
        print(f"Product ID {pid}: {p.title} - EXISTS, Country pricing: {p.product_country.count()}")
    except Products.DoesNotExist:
        print(f"Product ID {pid}: DOES NOT EXIST")
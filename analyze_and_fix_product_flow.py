import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries
from categories.models import Countries

print("=" * 80)
print("PRODUCT FLOW ANALYSIS AND FIX")
print("=" * 80)

# 1. Database Product Count
total_products = Products.objects.count()
active_products = Products.objects.filter(is_active=True, status=5).count()
print(f"\n1. DATABASE PRODUCT COUNT:")
print(f"   Total products: {total_products}")
print(f"   Active & Published products: {active_products}")

# 2. Homepage Products
print(f"\n2. HOMEPAGE PRODUCTS (hardcoded IDs: 1, 2, 3, 4, 29348, 29349):")
homepage_ids = [1, 2, 3, 4, 29348, 29349]
for pid in homepage_ids:
    try:
        product = Products.objects.get(id=pid)
        has_countries = ProductAvailableCountries.objects.filter(product=product).exists()
        print(f"   ID {pid}: {product.title} | Active: {product.is_active} | Status: {product.status} | Has Country Pricing: {has_countries}")
    except Products.DoesNotExist:
        print(f"   ID {pid}: DOES NOT EXIST")

# 3. Country Pricing Analysis
print(f"\n3. COUNTRY PRICING ANALYSIS:")
countries = Countries.objects.filter(is_active=True)
print(f"   Total active countries: {countries.count()}")

for country in countries:
    products_with_pricing = ProductAvailableCountries.objects.filter(country=country).count()
    print(f"   {country.country_code} ({country.currency_type}): {products_with_pricing} products")

# 4. Products without country pricing
print(f"\n4. PRODUCTS WITHOUT COUNTRY PRICING:")
products_without_countries = Products.objects.filter(
    is_active=True, 
    status=5
).exclude(
    id__in=ProductAvailableCountries.objects.values_list('product_id', flat=True)
)

if products_without_countries.exists():
    print(f"   Found {products_without_countries.count()} products without country pricing:")
    for product in products_without_countries[:10]:  # Show first 10
        print(f"   - ID {product.id}: {product.title} (SKU: {product.sku})")
else:
    print("   ✓ All active products have country pricing")

# 5. Check for test products
print(f"\n5. TEST PRODUCTS CHECK:")
test_products = Products.objects.filter(title__startswith='Test Product')
print(f"   Remaining test products: {test_products.count()}")
if test_products.exists():
    for p in test_products:
        print(f"   - ID {p.id}: {p.title}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
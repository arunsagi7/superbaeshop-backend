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
print("ADDING COUNTRY PRICING FOR ALL PRODUCTS")
print("=" * 80)

# Get all active products
products = Products.objects.filter(is_active=True, status=5)
print(f"\nTotal products to process: {products.count()}")

# Get all active countries
countries = Countries.objects.filter(is_active=True)
print(f"Total active countries: {countries.count()}")

# Sample prices from existing data (we'll use these as base)
sample_prices = {
    'ARS': {'original': 5000, 'selling': 4500},
    'AUD': {'original': 50, 'selling': 45},
    'INR': {'original': 500, 'selling': 450},
    'SGD': {'original': 20, 'selling': 18},
}

# Default prices for other currencies
default_prices = {
    'USD': {'original': 25, 'selling': 22},
    'EUR': {'original': 23, 'selling': 20},
    'GBP': {'original': 20, 'selling': 18},
    'CAD': {'original': 30, 'selling': 27},
    'AED': {'original': 90, 'selling': 81},
}

total_created = 0
total_skipped = 0

for product in products:
    print(f"\nProcessing: {product.title} (ID: {product.id})")
    product_countries_added = 0
    
    for country in countries:
        # Check if pricing already exists
        existing = ProductAvailableCountries.objects.filter(product=product, country=country).exists()
        
        if existing:
            total_skipped += 1
            continue
        
        # Determine price based on currency
        currency = country.currency_type
        
        if currency in sample_prices:
            prices = sample_prices[currency]
        elif currency in default_prices:
            prices = default_prices[currency]
        else:
            # Default fallback
            prices = {'original': 25, 'selling': 22}
        
        # Create pricing record
        ProductAvailableCountries.objects.create(
            product=product,
            country=country,
            original_price=prices['original'],
            selling_price=prices['selling'],
            promotion_text=""
        )
        product_countries_added += 1
        total_created += 1
    
    print(f"  Added pricing for {product_countries_added} new countries")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total products processed: {products.count()}")
print(f"Total pricing records created: {total_created}")
print(f"Total pricing records skipped (already existed): {total_skipped}")
print(f"\n✓ All products now have pricing in all {countries.count()} countries")
print("=" * 80)
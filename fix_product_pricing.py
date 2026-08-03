"""
Script to fix product pricing issues and remove duplicates
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from product_management.models import Products, ProductAvailableCountries
from categories.models import Countries

def fix_product_pricing():
    print("\n" + "="*60)
    print("FIXING PRODUCT PRICING AND REMOVING DUPLICATES")
    print("="*60)
    
    # Step 1: Delete duplicate products (202-205)
    print("\nStep 1: Removing duplicate products...")
    duplicate_ids = [202, 203, 204, 205]
    for prod_id in duplicate_ids:
        try:
            product = Products.objects.get(id=prod_id)
            print(f"  Deleting duplicate product {prod_id}: {product.title}")
            product.delete()
        except Products.DoesNotExist:
            print(f"  Product {prod_id} already deleted or doesn't exist")
    
    # Step 2: Update correct products (182-185) with homepage section prices
    print("\nStep 2: Updating correct product prices...")
    
    # Homepage section prices (product_id: {selling_price, original_price})
    homepage_prices = {
        182: {'selling': 12.99, 'original': 15.59},  # Pocket Notebook
        183: {'selling': 8.99, 'original': 10.79},   # Laptop Sticker
        184: {'selling': 19.99, 'original': 23.99},  # Sticker Book Large
        185: {'selling': 6.99, 'original': 8.39},    # To Do List
    }
    
    countries = Countries.objects.all()
    
    for product_id, prices in homepage_prices.items():
        try:
            product = Products.objects.get(id=product_id)
            print(f"\n  Updating Product {product_id}: {product.title}")
            print(f"    New prices: ${prices['selling']} (was ${prices['original']})")
            
            # Update all country pricing for this product
            updated_count = 0
            for country in countries:
                product_country = ProductAvailableCountries.objects.filter(
                    product=product,
                    country=country
                ).first()
                
                if product_country:
                    product_country.selling_price = prices['selling']
                    product_country.original_price = prices['original']
                    product_country.save()
                    updated_count += 1
            
            print(f"    ✓ Updated pricing for {updated_count} countries")
            
        except Products.DoesNotExist:
            print(f"    ✗ Product {product_id} not found!")
    
    print("\n" + "="*60)
    print("✓✓✓ PRODUCT PRICING FIXED SUCCESSFULLY ✓✓✓")
    print("="*60)
    print("\nWhat was done:")
    print("  1. Removed duplicate products (IDs: 202, 203, 204, 205)")
    print("  2. Updated correct products (IDs: 182, 183, 184, 185)")
    print("  3. Prices now match homepage sections exactly")
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    try:
        fix_product_pricing()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
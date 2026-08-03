import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries, ProductImages, ProductVideos, ProductContent
from cart_management.models import Cart

print("=" * 60)
print("DELETING SPECIFIC TEST PRODUCTS")
print("=" * 60)

# Target product IDs
target_ids = [207, 202]

print("\nStep 1: Checking if target products exist...")
for pid in target_ids:
    try:
        product = Products.objects.get(id=pid)
        print(f"  ✓ Product ID {pid}: {product.title} (SKU: {product.sku})")
    except Products.DoesNotExist:
        print(f"  ✗ Product ID {pid}: DOES NOT EXIST")

print("\nStep 2: Deleting related data and products...")
for pid in target_ids:
    try:
        product = Products.objects.get(id=pid)
        print(f"\n  Deleting Product ID {pid}: {product.title}")
        
        # Delete product available countries
        countries_count = ProductAvailableCountries.objects.filter(product=product).count()
        ProductAvailableCountries.objects.filter(product=product).delete()
        print(f"    - Deleted {countries_count} country pricing records")
        
        # Delete product images
        images_count = ProductImages.objects.filter(product=product).count()
        ProductImages.objects.filter(product=product).delete()
        print(f"    - Deleted {images_count} product images")
        
        # Delete product videos
        videos_count = ProductVideos.objects.filter(product=product).count()
        ProductVideos.objects.filter(product=product).delete()
        print(f"    - Deleted {videos_count} product videos")
        
        # Delete product content
        content_count = ProductContent.objects.filter(product=product).count()
        ProductContent.objects.filter(product=product).delete()
        print(f"    - Deleted {content_count} product content records")
        
        # Delete cart items referencing this product
        cart_count = Cart.objects.filter(product=product).count()
        Cart.objects.filter(product=product).delete()
        print(f"    - Deleted {cart_count} cart items")
        
        # Delete the product itself
        product.delete()
        print(f"    ✓ Product ID {pid} deleted successfully")
        
    except Products.DoesNotExist:
        print(f"  Product ID {pid}: DOES NOT EXIST, skipping...")

print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

# Verify deletion
for pid in target_ids:
    try:
        p = Products.objects.get(id=pid)
        print(f"  ✗ Product ID {pid}: {p.title} - STILL EXISTS (ERROR!)")
    except Products.DoesNotExist:
        print(f"  ✓ Product ID {pid}: DOES NOT EXIST (correctly removed)")

# Show remaining products
total = Products.objects.count()
print(f"\nTotal products in database: {total}")

# Check for any remaining test products
remaining_tests = Products.objects.filter(title__startswith='Test Product')
print(f"Remaining 'Test Product*' entries: {remaining_tests.count()}")
if remaining_tests.count() > 0:
    print("\nRemaining test products:")
    for p in remaining_tests:
        print(f"  ID:{p.id} - {p.title} - {p.sku}")

print("\n" + "=" * 60)
print("DELETION COMPLETE")
print("=" * 60)
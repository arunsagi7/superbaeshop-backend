import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries

print("Deleting test products (IDs 98, 99, 100, 101)...")

# Delete the test products
for pid in [98, 99, 100, 101]:
    try:
        product = Products.objects.get(id=pid)
        # Delete related product country pricing first
        ProductAvailableCountries.objects.filter(product=product).delete()
        product.delete()
        print(f"  Deleted product ID {pid}")
    except Products.DoesNotExist:
        print(f"  Product ID {pid} does not exist, skipping...")

print("\n=== VERIFICATION ===")
print(f"Total products now: {Products.objects.count()}")
for pid in [98, 99, 100, 101]:
    try:
        p = Products.objects.get(id=pid)
        print(f"Product ID {pid}: {p.title} - EXISTS")
    except Products.DoesNotExist:
        print(f"Product ID {pid}: DOES NOT EXIST (correctly removed)")

print("\nOriginal products (50, 51, 52, 53) still exist:")
for pid in [50, 51, 52, 53]:
    try:
        p = Products.objects.get(id=pid)
        print(f"  Product ID {pid}: {p.title} - EXISTS")
    except Products.DoesNotExist:
        print(f"  Product ID {pid}: DOES NOT EXIST")
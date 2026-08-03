import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries
from cart_management.models import CartItem, CartList

print("Finding test products...")
test_products = Products.objects.filter(title__startswith='Test Product')
print(f"Found {test_products.count()} test products")

for product in test_products:
    print(f"  ID:{product.id} - {product.title} - {product.sku}")

print("\nDeleting related data and products...")
for product in test_products:
    pid = product.id
    # Delete product available countries
    ProductAvailableCountries.objects.filter(product=product).delete()
    # Delete cart items referencing this product
    CartItem.objects.filter(product=product).delete()
    # Delete the product itself
    product.delete()
    print(f"  Deleted product ID {pid}")

print("\n=== VERIFICATION ===")
remaining = Products.objects.filter(title__startswith='Test Product')
print(f"Remaining test products: {remaining.count()}")
total = Products.objects.count()
print(f"Total products now: {total}")
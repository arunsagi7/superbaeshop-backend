import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products
from django.conf import settings

print("=== CHECKING PRODUCT IMAGES ===")
for product in Products.objects.all()[:5]:
    print(f"Product: {product.title}")
    print(f"  thumbnail_image: {product.thumbnail_image}")
    if product.thumbnail_image:
        full_path = os.path.join(settings.MEDIA_ROOT, str(product.thumbnail_image))
        print(f"  Full path: {full_path}")
        print(f"  Exists: {os.path.exists(full_path)}")
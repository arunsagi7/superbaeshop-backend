import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from django.conf import settings

# Check media directory
media_root = settings.MEDIA_ROOT
print(f"Media root: {media_root}")
print(f"Media root exists: {os.path.exists(media_root)}")

# Check product images
product_images_dir = os.path.join(media_root, 'product', 'product-image')
print(f"\nProduct images dir: {product_images_dir}")
print(f"Product images dir exists: {os.path.exists(product_images_dir)}")

if os.path.exists(product_images_dir):
    files = os.listdir(product_images_dir)
    print(f"Files in product images dir: {len(files)}")
    for f in files[:5]:
        print(f"  - {f}")

# Check homepage products
homepage_products_dir = os.path.join(media_root, 'homepage_products')
print(f"\nHomepage products dir: {homepage_products_dir}")
print(f"Homepage products dir exists: {os.path.exists(homepage_products_dir)}")

if os.path.exists(homepage_products_dir):
    files = os.listdir(homepage_products_dir)
    print(f"Files in homepage products dir: {len(files)}")
    for f in files[:5]:
        print(f"  - {f}")
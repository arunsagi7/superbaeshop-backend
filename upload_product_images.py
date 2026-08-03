import os
import sys
import shutil
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductImages
from categories.models import HomepageSectionProduct
from django.conf import settings

# Source images directory (Next.js public folder)
NEXTJS_PUBLIC_IMAGES = r"d:\karthi\snb-old\space-and-beauty-nextjs\public\images"
# Django media directory
DJANGO_MEDIA_ROOT = settings.MEDIA_ROOT
DJANGO_MEDIA_URL = settings.MEDIA_URL

# Create media directory if it doesn't exist
os.makedirs(DJANGO_MEDIA_ROOT, exist_ok=True)

# Map product titles to image files (using productcard directory)
product_image_mapping = {
    'Daily Done Kit': 'productcard/product-1.png',
    'One Notebook a Month': 'productcard/product-2.png',
    'Mega Sticker Magic Pack': 'productcard/product-3.png',
    'Little Plans Big Days Set': 'productcard/product-4.png',
    'Sticker Book': 'productcard/product-5.png',
    'Laptop Sticker': 'productcard/product-6.png',
    'Stationery Collection': 'productcard/product-7.png',
    'Aqua Dream': 'productcard/product-1.png',
    'Lavender Haze': 'productcard/product-2.png',
    'Moonwave Laptop': 'productcard/product-3.png',
    'Lily Pond': 'productcard/product-4.png',
    '2000 Unlimited Sticker Book': 'productcard/product-5.png',
    'Mega Sticker Mega Pack': 'productcard/product-6.png',
    '1000 Unlimited Sticker Book': 'productcard/product-7.png',
    '1000 Sticker Book': 'productcard/product-1.png',
    'Pocket Notebook': 'productcard/product-1.png',
    'To Do List': 'productcard/product-2.png',
    'Pink Blossom Notebook': 'productcard/product-3.png',
    'Lavender Dots Diary': 'productcard/product-4.png',
    'Sky Blue Planner': 'productcard/product-5.png',
    'Mint Daisy Journal': 'productcard/product-6.png',
    'Rose Gold Notebook': 'productcard/product-7.png',
    'Pastel Washi Set': 'productcard/product-1.png',
    'Dreamy Cloud Notepad': 'productcard/product-1.png',
    'Spring Garden Diary': 'productcard/product-5.png',
    'Sticker Book Large': 'productcard/product-1.png',
}

def upload_images_to_database():
    print("=== UPLOADING PRODUCT IMAGES TO DATABASE ===\n")
    
    # Create product images directory in media
    product_images_dir = os.path.join(DJANGO_MEDIA_ROOT, 'product', 'product-image')
    os.makedirs(product_images_dir, exist_ok=True)
    
    updated_count = 0
    skipped_count = 0
    
    for product in Products.objects.all():
        # Get the image filename for this product
        image_filename = product_image_mapping.get(product.title)
        
        if not image_filename:
            print(f"  No image mapping for: {product.title}")
            skipped_count += 1
            continue
        
        # Source image path
        source_path = os.path.join(NEXTJS_PUBLIC_IMAGES, image_filename)
        
        if not os.path.exists(source_path):
            print(f"  Image file not found: {source_path}")
            skipped_count += 1
            continue
        
        # Destination path in media
        dest_path = os.path.join(product_images_dir, f"product_{product.id}_{os.path.basename(image_filename)}")
        
        # Copy the file
        try:
            shutil.copy2(source_path, dest_path)
            
            # Update the product's thumbnail_image field
            relative_path = f"product/product-image/product_{product.id}_{os.path.basename(image_filename)}"
            product.thumbnail_image = relative_path
            product.save()
            
            print(f"  Updated: {product.title} -> {relative_path}")
            updated_count += 1
            
        except Exception as e:
            print(f"  Error updating {product.title}: {e}")
            skipped_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Products updated: {updated_count}")
    print(f"Products skipped: {skipped_count}")
    
    # Also update HomepageSectionProduct images
    print("\n=== UPDATING HOMEPAGE SECTION PRODUCT IMAGES ===\n")
    
    for section in HomepageSectionProduct.objects.all():
        # Get the image name - could be string or ImageFieldFile
        image_name = str(section.image.name) if section.image and section.image.name else None
        
        if image_name and image_name.startswith('/images/'):
            # Extract the path after /images/
            image_path = image_name[8:]  # Remove '/images/'
            source_path = os.path.join(NEXTJS_PUBLIC_IMAGES, image_path)
            
            if os.path.exists(source_path):
                # Create destination directory
                dest_dir = os.path.join(DJANGO_MEDIA_ROOT, 'homepage_products')
                os.makedirs(dest_dir, exist_ok=True)
                
                # Get the filename
                image_filename = os.path.basename(image_path)
                dest_path = os.path.join(dest_dir, f"section_{section.id}_{image_filename}")
                
                try:
                    shutil.copy2(source_path, dest_path)
                    section.image = f"homepage_products/section_{section.id}_{image_filename}"
                    section.save()
                    print(f"  Updated section image: {section.title}")
                except Exception as e:
                    print(f"  Error updating section image {section.title}: {e}")
            else:
                print(f"  Image not found for {section.title}: {image_path}")
    
    print("\n=== DONE ===")

if __name__ == "__main__":
    upload_images_to_database()
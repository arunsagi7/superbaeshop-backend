"""
Script to fix homepage section product IDs to use correct products (182-185)
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from product_management.models import Products
from categories.models import HomepageSectionProduct, HomepageSection

def fix_homepage_product_ids():
    print("\n" + "="*60)
    print("FIXING HOMEPAGE SECTION PRODUCT IDs")
    print("="*60)
    
    # Correct product mapping based on titles
    correct_products = {
        'Pocket Notebook': 182,
        'Laptop Sticker': 183,
        'Sticker Book Large': 184,
        'To Do List': 185,
    }
    
    # Get hero section
    try:
        hero_section = HomepageSection.objects.get(section_type='hero')
        print(f"\n✓ Found hero section: {hero_section.title}")
    except HomepageSection.DoesNotExist:
        print("\n✗ Hero section not found!")
        return
    
    # Update each product in hero section
    print("\nUpdating hero section products...")
    for section_product in hero_section.section_products.all():
        old_product_id = section_product.product.id if section_product.product else None
        product_title = section_product.title
        
        print(f"\n  Section Product: {product_title}")
        print(f"    Old product ID: {old_product_id}")
        
        if product_title in correct_products:
            new_product_id = correct_products[product_title]
            try:
                new_product = Products.objects.get(id=new_product_id)
                section_product.product = new_product
                section_product.save()
                print(f"    ✓ Updated to product ID: {new_product_id}")
                print(f"      Product: {new_product.title}")
            except Products.DoesNotExist:
                print(f"    ✗ Product {new_product_id} not found!")
        else:
            print(f"    ⚠ No mapping found for this product")
    
    print("\n" + "="*60)
    print("✓✓✓ HOMEPAGE PRODUCT IDs FIXED ✓✓✓")
    print("="*60)
    print("\nHero section now uses correct product IDs:")
    for section_product in hero_section.section_products.all():
        if section_product.product:
            print(f"  - {section_product.title}: Product ID {section_product.product.id}")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        fix_homepage_product_ids()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
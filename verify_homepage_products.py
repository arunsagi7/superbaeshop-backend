"""
Script to verify homepage section products in database
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from categories.models import HomepageSection, HomepageSectionProduct
from product_management.models import Products

def verify_homepage_products():
    print("\n" + "="*60)
    print("VERIFYING HOMEPAGE SECTION PRODUCTS")
    print("="*60)
    
    try:
        hero_section = HomepageSection.objects.get(section_type='hero')
        print(f"\n✓ Hero Section: {hero_section.title}")
        print(f"  Total products: {hero_section.section_products.count()}")
        
        print("\n  Products in hero section:")
        for sp in hero_section.section_products.all().order_by('ordering'):
            product_id = sp.product.id if sp.product else None
            product_exists = Products.objects.filter(id=product_id).exists() if product_id else False
            status = "✓" if product_exists else "✗"
            print(f"    {status} {sp.title}")
            print(f"      - Section Product ID: {sp.id}")
            print(f"      - Product ID: {product_id}")
            print(f"      - Product exists: {product_exists}")
            if sp.product:
                print(f"      - Product SKU: {sp.product.sku}")
        
        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("="*60)
        
        # Check if any products are missing
        missing = []
        for sp in hero_section.section_products.all():
            if not sp.product or not Products.objects.filter(id=sp.product.id).exists():
                missing.append(sp.title)
        
        if missing:
            print(f"\n⚠ WARNING: {len(missing)} products are missing!")
            for title in missing:
                print(f"  - {title}")
        else:
            print("\n✓ All products exist in database!")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_homepage_products()
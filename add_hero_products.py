"""
Script to add hero section products (IDs 182-185)
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from product_management.models import Products, ProductAvailableCountries
from categories.models import Categories, SubCategories, Countries
from django.core.files.base import ContentFile
import requests

def get_or_create_category():
    """Get or create a default category"""
    category = Categories.objects.first()
    if not category:
        # Create super category first
        from supercategories.models import SuperCategories
        super_cat = SuperCategories.objects.create(
            title="Stationery",
            code="ST"
        )
        category = Categories.objects.create(
            super_category=super_cat,
            title="Notebooks & Diaries",
            code="NB"
        )
    return category

def get_or_create_subcategory(category):
    """Get or create a default subcategory"""
    subcategory = SubCategories.objects.filter(category=category).first()
    if not subcategory:
        subcategory = SubCategories.objects.create(
            category=category,
            title="Premium Diaries",
            code="PD"
        )
    return subcategory

def get_countries():
    """Get all available countries"""
    return Countries.objects.all()

def create_product(product_id, title, sku, slug):
    """Create a product with the given ID"""
    category = get_or_create_category()
    subcategory = get_or_create_subcategory(category)
    
    # Delete if exists
    Products.objects.filter(id=product_id).delete()
    
    # Create product
    product = Products.objects.create(
        id=product_id,
        sku=sku,
        title=title,
        slug=slug,
        category=category,
        sub_category=subcategory,
        support_number='1234567890',
        stock_qty=100,
        weight=1.0,
        affiliate_percentage=5,
        status=5,  # Published
        is_active=True
    )
    
    print(f"✓ Created product: {product.title} (ID: {product.id})")
    return product

def add_country_pricing(product, country, original_price, selling_price):
    """Add country-specific pricing for a product"""
    pricing, created = ProductAvailableCountries.objects.get_or_create(
        product=product,
        country=country,
        defaults={
            'original_price': original_price,
            'selling_price': selling_price
        }
    )
    if created:
        print(f"  ✓ Added pricing for {country.title}: ${selling_price}")
    return pricing

def main():
    print("\n" + "="*60)
    print("ADDING HERO SECTION PRODUCTS")
    print("="*60)
    
    # Get all countries
    countries = get_countries()
    print(f"\n✓ Found {countries.count()} countries in database")
    
    # Product 182 - Pocket Notebook
    print("\nCreating Product 182: Pocket Notebook")
    product_182 = create_product(182, 'Pocket Notebook', 'SKU-POCKET-182', 'pocket-notebook')
    for country in countries:
        add_country_pricing(product_182, country, 15, 12)
    
    # Product 183 - Laptop Sticker
    print("\nCreating Product 183: Laptop Sticker")
    product_183 = create_product(183, 'Laptop Sticker', 'SKU-STICKER-183', 'laptop-sticker')
    for country in countries:
        add_country_pricing(product_183, country, 10, 8)
    
    # Product 184 - Sticker Book Large
    print("\nCreating Product 184: Sticker Book Large")
    product_184 = create_product(184, 'Sticker Book Large', 'SKU-STICKERBOOK-184', 'sticker-book-large')
    for country in countries:
        add_country_pricing(product_184, country, 25, 20)
    
    # Product 185 - To Do List
    print("\nCreating Product 185: To Do List")
    product_185 = create_product(185, 'To Do List', 'SKU-TODO-185', 'to-do-list')
    for country in countries:
        add_country_pricing(product_185, country, 12, 9)
    
    print("\n" + "="*60)
    print("✓✓✓ ALL PRODUCTS CREATED SUCCESSFULLY ✓✓✓")
    print("="*60)
    print("\nProducts can now be added to cart from the hero section!")
    print("\nProduct IDs: 182, 183, 184, 185")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
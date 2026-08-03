import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from product_management.models import Products, ProductAvailableCountries
from categories.models import Categories, SubCategories, Countries, HomepageSection, HomepageSectionProduct

# Create products 182-185
category = Categories.objects.first()
if not category:
    from supercategories.models import SuperCategories
    super_cat = SuperCategories.objects.create(title="Stationery", code="ST")
    category = Categories.objects.create(super_category=super_cat, title="Notebooks & Diaries", code="NB")

subcategory = SubCategories.objects.filter(category=category).first()
if not subcategory:
    subcategory = SubCategories.objects.create(category=category, title="Premium Diaries", code="PD")

countries = list(Countries.objects.all())

products_data = [
    (182, 'Pocket Notebook', 'SKU-POCKET-182', 'pocket-notebook', 12, 15),
    (183, 'Laptop Sticker', 'SKU-STICKER-183', 'laptop-sticker', 8, 10),
    (184, 'Sticker Book Large', 'SKU-STICKERBOOK-184', 'sticker-book-large', 20, 25),
    (185, 'To Do List', 'SKU-TODO-185', 'to-do-list', 9, 12),
]

for product_id, title, sku, slug, selling_price, original_price in products_data:
    Products.objects.filter(id=product_id).delete()
    product = Products.objects.create(
        id=product_id, sku=sku, title=title, slug=slug,
        category=category, sub_category=subcategory,
        support_number='1234567890', stock_qty=100, weight=1.0,
        affiliate_percentage=5, status=5, is_active=True
    )
    for country in countries:
        ProductAvailableCountries.objects.get_or_create(
            product=product, country=country,
            defaults={'original_price': original_price, 'selling_price': selling_price}
        )
    print(f"Created product: {title} (ID: {product_id})")

# Update hero section
hero_section = HomepageSection.objects.get(section_type='hero')
correct_products = {
    'Pocket Notebook': 182,
    'Laptop Sticker': 183,
    'Sticker Book Large': 184,
    'To Do List': 185,
}

for sp in hero_section.section_products.all():
    if sp.title in correct_products:
        new_product = Products.objects.get(id=correct_products[sp.title])
        sp.product = new_product
        sp.save()
        print(f"Updated {sp.title} to use product ID {correct_products[sp.title]}")

print("\nDone!")
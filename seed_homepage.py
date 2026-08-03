import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from product_management.models import Products, ProductAvailableCountries
from categories.models import HomepageSection, HomepageSectionProduct, Categories, SuperCategories, Countries
from django.utils.text import slugify
import random

# Step 1: Delete all existing products
print("Deleting all existing products...")
Products.objects.all().delete()
HomepageSectionProduct.objects.all().delete()
print("Done. Products remaining:", Products.objects.count())

# Step 2: Create categories
sc, _ = SuperCategories.objects.get_or_create(code="PR", title="Products", defaults={"is_active": True})
cat_stickers, _ = Categories.objects.get_or_create(super_category=sc, code="STK", title="Stickers", defaults={"is_active": True})
cat_notebooks, _ = Categories.objects.get_or_create(super_category=sc, code="NTB", title="Notebooks", defaults={"is_active": True})
cat_planners, _ = Categories.objects.get_or_create(super_category=sc, code="PLN", title="Planners", defaults={"is_active": True})
cat_stationery, _ = Categories.objects.get_or_create(super_category=sc, code="STN", title="Stationery", defaults={"is_active": True})

# Step 3: Create homepage sections
sections_data = {
    'hero': {'title': 'Hero Banner', 'subtitle': 'Welcome to', 'description': 'Discover beautiful stationery'},
    'product_grid': {'title': 'Product Grid', 'subtitle': 'Make you look', 'description': 'Trending products'},
    'promotional_banner': {'title': 'Promotional Banner', 'subtitle': '', 'description': 'Limited time deals'},
    'cute_collection': {'title': 'Cute Collection', 'subtitle': 'Cute', 'description': 'Premium stationery essentials crafted for radiant skin and everyday luxury.'},
    'customers_top_choice': {'title': "Customer's Top Choice", 'subtitle': "Customer's Top", 'description': 'Handpicked favorites our customers can\'t stop raving about'},
    'cute_collection_cards': {'title': 'Cute Collection Cards', 'subtitle': 'Cute', 'description': 'Adorable picks that bring joy to every page you write'},
    'dream_box_collections': {'title': 'Dream Box Collections', 'subtitle': 'Dream Box', 'description': 'Upgrade every day with connected devices delivering effortless performance.'},
    'testimonials': {'title': 'Testimonials', 'subtitle': 'What Our', 'description': 'Real reviews from real customers'},
    'upgrade_essentials': {'title': 'Upgrade Essentials', 'subtitle': 'Upgrade Your', 'description': 'Premium quality that makes every moment special'},
}

sections = {}
for st, info in sections_data.items():
    section, _ = HomepageSection.objects.get_or_create(
        section_type=st,
        defaults={
            'title': info['title'],
            'subtitle': info['subtitle'],
            'description': info['description'],
            'background_color': '',
            'link_url': '',
            'link_text': 'Shop Now',
            'is_active': True,
            'ordering': 0
        }
    )
    sections[st] = section

# Helper function
def create_product_with_country(title, category, prices_dict, stock=100, product_id=None):
    slug = slugify(title)
    # Generate unique SKU
    while True:
        sku = f"SKU-{random.randint(1000, 9999)}"
        if not Products.objects.filter(sku=sku).exists():
            break
    
    product_data = {
        'sku': sku,
        'title': title,
        'slug': slug,
        'category': category,
        'support_number': "9999999999",
        'stock_qty': stock,
        'weight': random.uniform(0.1, 2.0),
        'is_active': True,
        'status': 5
    }
    if product_id:
        product_data['id'] = product_id
    
    product = Products.objects.create(**product_data)
    
    for country_code2, price_data in prices_dict.items():
        country = Countries.objects.get(code2=country_code2)
        ProductAvailableCountries.objects.create(
            product=product,
            country=country,
            original_price=price_data.get('original_price', price_data['price'] * 1.2),
            selling_price=price_data['price']
        )
    return product

print("\nCreating products from screenshots...")

# ============ CUSTOMER'S TOP CHOICE (using productcard images) ============
print("\n1. Customer's Top Choice")
ctc_products = [
    ('Daily Done Kit', cat_notebooks, {'in': 29.99, 'au': 44.99, 'sg': 39.99, 'ar': 35.99}, 'Daily Done Kit', 4.9, 200),
    ('One Notebook a Month', cat_notebooks, {'in': 24.99, 'au': 37.99, 'sg': 33.99, 'ar': 29.99}, 'One Notebook a Month', 4.8, 150),
    ('Mega Sticker Magic Pack', cat_stickers, {'in': 34.99, 'au': 52.99, 'sg': 46.99, 'ar': 41.99}, 'Mega Sticker Magic Pack', 4.7, 180),
    ('Little Plans Big Days Set', cat_planners, {'in': 39.99, 'au': 59.99, 'sg': 53.99, 'ar': 47.99}, 'Little Plans, Big Days Set', 4.9, 90),
]

for i, (title, category, prices, subtitle, rating, reviews) in enumerate(ctc_products):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    HomepageSectionProduct.objects.create(
        section=sections['customers_top_choice'],
        title=title,
        subtitle=subtitle,
        image=f'/images/productcard/product-{i+1}.png',  # Fixed: using correct filename format
        price=prices['in'],
        rating=rating,
        reviews_count=reviews,
        link_text='Shop Now',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

# ============ CUTE COLLECTION (using cutecard images) ============
print("\n2. Cute Collection")
cute_products = [
    ('Sticker Book', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 23.99}, 'Sticker Book', 4.8, 156),
    ('Laptop Sticker', cat_stickers, {'in': 12.99, 'au': 18.99, 'sg': 16.99, 'ar': 14.99}, 'Laptop Sticker', 4.7, 134),
    ('Stationery Collection', cat_stationery, {'in': 24.99, 'au': 36.99, 'sg': 32.99, 'ar': 29.99}, 'Stationery Collection', 4.9, 201),
]

for i, (title, category, prices, subtitle, rating, reviews) in enumerate(cute_products):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    HomepageSectionProduct.objects.create(
        section=sections['cute_collection'],
        title=title,
        subtitle=subtitle,
        image=f'/images/cutecard/card-{i+1}.png',  # Fixed: using correct filename format
        price=prices['in'],
        rating=rating,
        reviews_count=reviews,
        link_text='Buy Now',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

# ============ CUTE COLLECTION CARDS (using cutecard images) ============
print("\n3. Cute Collection Cards")
cute_cards = [
    ('Aqua Dream', cat_stickers, {'in': 24.99, 'au': 36.99, 'sg': 32.99, 'ar': 29.99}, 'STICKERS', 4.9, 78),
    ('Lavender Haze', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 23.99}, 'STICKERS', 4.8, 134),
    ('Moonwave Laptop', cat_stickers, {'in': 22.99, 'au': 33.99, 'sg': 30.99, 'ar': 27.99}, 'STICKERS', 4.7, 56),
    ('Lily Pond', cat_stickers, {'in': 21.99, 'au': 32.99, 'sg': 29.99, 'ar': 26.99}, 'STICKERS', 4.9, 201),
]

for i, (title, category, prices, subtitle, rating, reviews) in enumerate(cute_cards):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    # Use card-1.png for index 3 (Lily Pond) since only 3 cards exist
    card_index = (i % 3) + 1
    HomepageSectionProduct.objects.create(
        section=sections['cute_collection_cards'],
        title=title,
        subtitle=subtitle,
        image=f'/images/cutecard/card-{card_index}.png',
        price=prices['in'],
        original_price=round(prices['in'] * 1.15, 2),
        rating=rating,
        reviews_count=reviews,
        link_text='Add to Cart',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

# ============ DREAM BOX COLLECTIONS (using dreambox images) ============
print("\n4. Dream Box Collections")
dream_box = [
    ('2000 Unlimited Sticker Book', cat_stickers, {'in': 39.99, 'au': 59.99, 'sg': 53.99, 'ar': 47.99}, 5.0, 89),
    ('Mega Sticker Mega Pack', cat_stickers, {'in': 29.99, 'au': 44.99, 'sg': 39.99, 'ar': 35.99}, 4.8, 156),
    ('1000 Unlimited Sticker Book', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 23.99}, 4.9, 234),
]

for i, (title, category, prices, rating, reviews) in enumerate(dream_box):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    HomepageSectionProduct.objects.create(
        section=sections['dream_box_collections'],
        title=title,
        image=f'/images/dreambox/card-{i+1}.png',  # Fixed: using correct filename format
        price=prices['in'],
        original_price=round(prices['in'] * 1.25, 2),
        rating=rating,
        reviews_count=reviews,
        link_text='VIEW PRODUCT',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

# ============ TESTIMONIALS (using customer images) ============
print("\n5. Testimonials")
testimonials = [
    ('1000 Sticker Book', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 23.99}, '', 4.9, 234),
    ('Pocket Notebook', cat_notebooks, {'in': 12.99, 'au': 18.99, 'sg': 16.99, 'ar': 15.99}, 'Best Seller', 4.8, 189),
    ('Dreamy Planner', cat_planners, {'in': 24.99, 'au': 36.99, 'sg': 32.99, 'ar': 29.99}, '', 4.7, 145),
    ('Pastel Washi Set', cat_stickers, {'in': 8.99, 'au': 12.99, 'sg': 11.99, 'ar': 10.99}, 'Popular', 4.9, 312),
    ('Lavender Dots Diary', cat_notebooks, {'in': 14.99, 'au': 21.99, 'sg': 19.99, 'ar': 17.99}, '', 4.6, 98),
]

for i, (title, category, prices, badge, rating, reviews) in enumerate(testimonials):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    HomepageSectionProduct.objects.create(
        section=sections['testimonials'],
        title=title,
        image=f'/images/customer/customercard-{i+1}.png',  # Fixed: using correct filename format
        price=prices['in'],
        badge=badge,
        rating=rating,
        reviews_count=reviews,
        link_text='Buy Now',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

# ============ UPGRADE ESSENTIALS (using upgrade images) ============
print("\n6. Upgrade Essentials")
upgrade_features = [
    ('Smart Headphone', 'Perfect for work or travel.', 'smart-headphone'),
    ('Smart Headphone', 'Perfect for work or travel.', 'smart-headphone'),
    ('Smart Headphone', 'Perfect for work or travel.', 'smart-headphone'),
    ('Smart Headphone', 'Perfect for work or travel.', 'smart-headphone'),
]

for i, (title, subtitle, badge) in enumerate(upgrade_features):
    HomepageSectionProduct.objects.create(
        section=sections['upgrade_essentials'],
        title=title,
        subtitle=subtitle,
        image=f'/images/upgrade/upgradebanner.png',  # Fixed: using correct filename format
        price=0,
        badge=badge,
        link_text='',
        ordering=i,
        is_active=True
    )
    print(f"  - {title}")

# ============ HERO SECTION (using heroimage images) ============
print("\n7. Hero Section")
hero_products = [
    (182, 'Pocket Notebook', cat_notebooks, {'in': 12.99, 'au': 18.99, 'sg': 16.99, 'ar': 15.99}, 'New', 4.5, 124),
    (183, 'Laptop Sticker', cat_stickers, {'in': 8.99, 'au': 12.99, 'sg': 11.99, 'ar': 10.99}, 'New', 4.8, 89),
    (184, 'Sticker Book Large', cat_stickers, {'in': 19.99, 'au': 29.99, 'sg': 26.99, 'ar': 24.99}, 'New', 4.9, 156),
    (185, 'To Do List', cat_notebooks, {'in': 6.99, 'au': 9.99, 'sg': 8.99, 'ar': 7.99}, 'New', 4.6, 203),
]

for i, (product_id, title, category, prices, badge, rating, reviews) in enumerate(hero_products):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()}, product_id=product_id)
    HomepageSectionProduct.objects.create(
        section=sections['hero'],
        title=title,
        subtitle='New',
        image=f'/images/heroimage/{["notebook", "laptopsticker", "stickerbook", "todolist"][i]}.png',
        price=prices['in'],
        original_price=round(prices['in'] * 1.2, 2),
        badge=badge,
        rating=rating,
        reviews_count=reviews,
        link_text='Buy Now',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title} (ID: {product_id})")

# ============ PRODUCT GRID (using productcard images) ============
print("\n8. Product Grid")
grid_products = [
    ('Pink Blossom Notebook', cat_notebooks, {'in': 12.99, 'au': 18.99, 'sg': 16.99, 'ar': 15.99}, 'Popular', 4.8, 124),
    ('Lavender Dots Diary', cat_notebooks, {'in': 14.99, 'au': 21.99, 'sg': 19.99, 'ar': 17.99}, '', 4.9, 89),
    ('Sky Blue Planner', cat_planners, {'in': 18.99, 'au': 27.99, 'sg': 24.99, 'ar': 22.99}, '', 4.7, 156),
    ('Mint Daisy Journal', cat_notebooks, {'in': 11.99, 'au': 17.99, 'sg': 15.99, 'ar': 14.99}, 'New', 4.6, 203),
    ('Rose Gold Notebook', cat_notebooks, {'in': 15.99, 'au': 23.99, 'sg': 20.99, 'ar': 18.99}, '', 4.8, 178),
    ('Pastel Washi Set', cat_stickers, {'in': 8.99, 'au': 12.99, 'sg': 11.99, 'ar': 10.99}, 'Best Value', 4.7, 267),
    ('Dreamy Cloud Notepad', cat_notebooks, {'in': 10.99, 'au': 15.99, 'sg': 14.99, 'ar': 12.99}, '', 4.5, 145),
    ('Spring Garden Diary', cat_notebooks, {'in': 13.99, 'au': 19.99, 'sg': 17.99, 'ar': 16.99}, '', 4.9, 92),
]

for i, (title, category, prices, badge, rating, reviews) in enumerate(grid_products):
    p = create_product_with_country(title, category, {k: {'price': v} for k, v in prices.items()})
    # Use product-1.png for index 7 (Spring Garden Diary) since only 7 products exist
    product_index = (i % 7) + 1
    HomepageSectionProduct.objects.create(
        section=sections['product_grid'],
        title=title,
        image=f'/images/productcard/product-{product_index}.png',
        price=prices['in'],
        original_price=round(prices['in'] * 1.2, 2) if badge else None,
        badge=badge,
        rating=rating,
        reviews_count=reviews,
        link_text='Buy Now',
        ordering=i,
        is_active=True,
        product=p
    )
    print(f"  - {title}")

print("\n=== SEEDING COMPLETE ===")
print(f"Total Products: {Products.objects.count()}")
print(f"Total Homepage Sections: {HomepageSection.objects.count()}")
print(f"Total Section Products: {HomepageSectionProduct.objects.count()}")
for s in HomepageSection.objects.all():
    count = s.section_products.count()
    print(f"  - {s.section_type}: {s.title} ({count} products)")

print("\n=== PRODUCT PRICING BY COUNTRY (Sample) ===")
for p in Products.objects.all()[:3]:
    print(f"\n{p.title}:")
    for pac in p.product_country.all():
        print(f"  {pac.country.title}: {pac.country.currency_type}{pac.selling_price} (was {pac.country.currency_type}{pac.original_price})")
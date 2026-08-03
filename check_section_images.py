import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from categories.models import HomepageSectionProduct

print("=== HOMEPAGE SECTION PRODUCTS ===\n")
for section in HomepageSectionProduct.objects.all():
    print(f"ID={section.id}, Title={section.title}, Image={section.image}, Image type={type(section.image)}")
    if section.image and section.image.name:
        print(f"  Image name: {section.image.name}")
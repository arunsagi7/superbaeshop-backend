from django.core.management.base import BaseCommand
from categories.models import HeroBanner, HomepageSection

class Command(BaseCommand):
    help = 'Seed Hero Banner table with banner-1, banner-2, banner-3'

    def handle(self, *args, **kwargs):
        HeroBanner.objects.all().delete()
        
        # Link to first homepage section as a demo
        section = HomepageSection.objects.first()

        banners = [
            {'title': 'Banner 1', 'video': 'hero_banners/videos/banner-1.mp4', 'ordering': 0, 'section': section},
            {'title': 'Banner 2', 'video': 'hero_banners/videos/banner-2.mp4', 'ordering': 1, 'section': section},
            {'title': 'Banner 3', 'video': 'hero_banners/videos/banner-3.mp4', 'ordering': 2, 'section': section},
        ]

        for b in banners:
            banner, created = HeroBanner.objects.get_or_create(
                title=b['title'],
                defaults={
                    'video': b['video'],
                    'ordering': b['ordering'],
                    'section': b['section'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {banner.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated {banner.title}"))
        self.stdout.write(self.style.SUCCESS("Successfully seeded hero banners."))

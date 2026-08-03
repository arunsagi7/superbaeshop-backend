import os
from django.core.management.base import BaseCommand
from django.conf import settings
from hero.models import HeroVideo

class Command(BaseCommand):
    help = 'Load hero banner videos from the frontend public folder into the database.'

    def handle(self, *args, **options):
        # Path to the video files in the Next.js project
        video_dir = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'space-and-beauty-nextjs', 'public', 'images', 'heroimage'))
        if not os.path.isdir(video_dir):
            self.stdout.write(self.style.ERROR(f'Video directory does not exist: {video_dir}'))
            return

        # List video files (accept any extension, but typical .mp4)
        video_files = [f for f in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, f)) and f.lower().endswith(('.mp4', '.webm', '.ogg'))]
        if not video_files:
            self.stdout.write(self.style.WARNING('No video files found in the directory.'))
            return

        # Sort to have deterministic order
        video_files.sort()
        for idx, filename in enumerate(video_files, start=1):
            title = os.path.splitext(filename)[0].replace('_', ' ').title()
            # Check if already exists
            if HeroVideo.objects.filter(title=title).exists():
                self.stdout.write(self.style.NOTICE(f'Skipping existing video: {title}'))
                continue
            # Copy file into MEDIA_ROOT/hero_videos (Django will handle via FileField)
            src_path = os.path.join(video_dir, filename)
            # Open the file and let Django save it
            with open(src_path, 'rb') as f:
                hero = HeroVideo(title=title, order=idx, is_active=True)
                hero.video.save(filename, f, save=True)
                self.stdout.write(self.style.SUCCESS(f'Added HeroVideo: {title}'))

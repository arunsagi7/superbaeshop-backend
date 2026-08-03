from django.db import models

class HeroVideo(models.Model):
    title = models.CharField(max_length=100, blank=True)
    video = models.FileField(upload_to='hero_videos/')
    order = models.PositiveIntegerField(default=0, help_text='Playback order')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Herobanner'
        verbose_name_plural = 'Herobanners'

    def __str__(self):
        return self.title or f'Video {self.id}'

class HeroVideoProduct(models.Model):
    video = models.ForeignKey(HeroVideo, related_name='products', on_delete=models.CASCADE)
    product = models.ForeignKey('product_management.Products', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('video', 'product')

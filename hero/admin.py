from django.contrib import admin
from .models import HeroVideo, HeroVideoProduct

class HeroVideoProductInline(admin.TabularInline):
    model = HeroVideoProduct
    extra = 1

@admin.register(HeroVideo)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    ordering = ('order',)
    inlines = [HeroVideoProductInline]

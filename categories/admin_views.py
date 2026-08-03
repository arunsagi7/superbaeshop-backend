import decimal
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages

from categories import models


class HomebannerListView(View):
    template_name = 'admin/homebanner_list.html'

    def get(self, request):
        banners = models.HeroBanner.objects.all().order_by('ordering')
        return render(request, self.template_name, {'banners': banners})


class HomebannerCreateView(View):
    template_name = 'admin/homebanner_form.html'

    def get(self, request):
        products = models.HeroBannerProduct.objects.none()
        return render(request, self.template_name, {
            'banner': None,
            'products': products,
            'form_url': '/homebanner/add/',
        })

    def post(self, request):
        title = request.POST.get('title', '').strip()
        ordering = request.POST.get('ordering', 0)
        is_active = request.POST.get('is_active', 'on') == 'on'
        video_file = request.FILES.get('video')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('/homebanner/add/')

        if not video_file:
            messages.error(request, 'Video file is required.')
            return redirect('/homebanner/add/')

        banner = models.HeroBanner.objects.create(
            title=title,
            video=video_file,
            ordering=ordering,
            is_active=is_active,
        )

        product_titles = request.POST.getlist('product_title[]')
        product_prices = request.POST.getlist('product_price[]')
        product_images = request.POST.getlist('product_image[]')
        product_ratings = request.POST.getlist('product_rating[]')
        product_reviews = request.POST.getlist('product_reviews_count[]')
        product_badges = request.POST.getlist('product_badge[]')
        product_link_texts = request.POST.getlist('product_link_text[]')
        product_ids = request.POST.getlist('product_id[]')

        for i in range(len(product_titles)):
            if product_titles[i].strip():
                prod_id = product_ids[i].strip() if i < len(product_ids) else ''
                product_obj = None
                if prod_id and prod_id.isdigit():
                    from product_management.models import Products
                    try:
                        product_obj = Products.objects.get(id=int(prod_id))
                    except Products.DoesNotExist:
                        pass
                def safe_decimal(val, default=0):
                    try:
                        return decimal.Decimal(str(val)) if val and str(val).strip() else decimal.Decimal(default)
                    except (decimal.InvalidOperation, ValueError):
                        return decimal.Decimal(default)
                
                def safe_int(val, default=0):
                    try:
                        return int(val) if val and str(val).strip() else default
                    except (ValueError, TypeError):
                        return default
                
                models.HeroBannerProduct.objects.create(
                    banner=banner,
                    product=product_obj,
                    title=product_titles[i].strip(),
                    price=safe_decimal(product_prices[i] if i < len(product_prices) else '', 0),
                    image=product_images[i] if i < len(product_images) else '',
                    rating=safe_decimal(product_ratings[i] if i < len(product_ratings) else '', 4.5),
                    reviews_count=safe_int(product_reviews[i] if i < len(product_reviews) else '', 0),
                    badge=product_badges[i] if i < len(product_badges) else '',
                    link_text=product_link_texts[i] if i < len(product_link_texts) else 'Buy Now',
                    ordering=i,
                )

        messages.success(request, f'Banner "{title}" created successfully.')
        return redirect('/homebanner/')


class HomebannerEditView(View):
    template_name = 'admin/homebanner_form.html'

    def get(self, request, banner_id):
        banner = get_object_or_404(models.HeroBanner, id=banner_id)
        products = banner.banner_products.all().order_by('ordering')
        return render(request, self.template_name, {
            'banner': banner,
            'products': products,
            'form_url': f'/homebanner/{banner_id}/edit/',
        })

    def post(self, request, banner_id):
        banner = get_object_or_404(models.HeroBanner, id=banner_id)
        title = request.POST.get('title', '').strip()
        ordering = request.POST.get('ordering', 0)
        is_active = request.POST.get('is_active', 'on') == 'on'
        video_file = request.FILES.get('video')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(f'/homebanner/{banner_id}/edit/')

        banner.title = title
        banner.ordering = ordering
        banner.is_active = is_active
        if video_file:
            banner.video = video_file
        banner.save()

        banner.banner_products.all().delete()

        product_titles = request.POST.getlist('product_title[]')
        product_prices = request.POST.getlist('product_price[]')
        product_images = request.POST.getlist('product_image[]')
        product_ratings = request.POST.getlist('product_rating[]')
        product_reviews = request.POST.getlist('product_reviews_count[]')
        product_badges = request.POST.getlist('product_badge[]')
        product_link_texts = request.POST.getlist('product_link_text[]')
        product_ids = request.POST.getlist('product_id[]')

        for i in range(len(product_titles)):
            if product_titles[i].strip():
                prod_id = product_ids[i].strip() if i < len(product_ids) else ''
                product_obj = None
                if prod_id and prod_id.isdigit():
                    from product_management.models import Products
                    try:
                        product_obj = Products.objects.get(id=int(prod_id))
                    except Products.DoesNotExist:
                        pass
                def safe_decimal(val, default=0):
                    try:
                        return decimal.Decimal(str(val)) if val and str(val).strip() else decimal.Decimal(default)
                    except (decimal.InvalidOperation, ValueError):
                        return decimal.Decimal(default)
                
                def safe_int(val, default=0):
                    try:
                        return int(val) if val and str(val).strip() else default
                    except (ValueError, TypeError):
                        return default
                
                models.HeroBannerProduct.objects.create(
                    banner=banner,
                    product=product_obj,
                    title=product_titles[i].strip(),
                    price=safe_decimal(product_prices[i] if i < len(product_prices) else '', 0),
                    image=product_images[i] if i < len(product_images) else '',
                    rating=safe_decimal(product_ratings[i] if i < len(product_ratings) else '', 4.5),
                    reviews_count=safe_int(product_reviews[i] if i < len(product_reviews) else '', 0),
                    badge=product_badges[i] if i < len(product_badges) else '',
                    link_text=product_link_texts[i] if i < len(product_link_texts) else 'Buy Now',
                    ordering=i,
                )

        messages.success(request, f'Banner "{title}" updated successfully.')
        return redirect('/homebanner/')


class HomebannerToggleView(View):
    def post(self, request, banner_id):
        banner = get_object_or_404(models.HeroBanner, id=banner_id)
        banner.is_active = not banner.is_active
        banner.save()
        return JsonResponse({'success': True, 'is_active': banner.is_active})


class HomebannerDeleteView(View):
    def post(self, request, banner_id):
        banner = get_object_or_404(models.HeroBanner, id=banner_id)
        title = banner.title
        banner.delete()
        messages.success(request, f'Banner "{title}" deleted successfully.')
        return redirect('/homebanner/')


class ProductSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        from product_management.models import Products
        products = Products.objects.filter(is_active=True)
        if q:
            products = products.filter(title__icontains=q)
        products = products.order_by('title')[:20]
        
        data = []
        for p in products:
            image_url = ''
            if p.thumbnail_image:
                image_url = p.thumbnail_image.url
            else:
                first_image = p.product_images.first()
                if first_image and first_image.image:
                    image_url = first_image.image.url
            
            data.append({
                'id': p.id, 
                'title': p.title, 
                'image': image_url
            })
        
        return JsonResponse({'products': data})

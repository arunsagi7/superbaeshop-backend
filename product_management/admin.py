import csv
from datetime import datetime

from annoying.functions import get_object_or_None
from django.contrib import admin
from django import forms
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django_summernote.admin import SummernoteInlineModelAdmin
from suit.admin import RelatedFieldAdmin

from categories.admin import my_admin_site
from categories.models import Categories, SuperCategories
from product_management import models, utils


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

    def clean(self):
        if not (self.cleaned_data['csv_file'] or self.cleaned_data['csv_file'].endswith(".csv")):
            raise forms.ValidationError(
                'Please enter your code in text box or upload an appropriate file.')
        return self.cleaned_data


class ProductImagesAdminInline(admin.StackedInline):
    model = models.ProductImages
    fields = ("title", "image", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            from django.utils.safestring import mark_safe
            image_url = obj.image.url
            if image_url.startswith('http'):
                return mark_safe(
                    f'<img src="{image_url}" width="100" height="100" style="object-fit:cover;border-radius:4px" />')
            return mark_safe(
                f'<img src="https://api.spaceandbeauty.com{image_url}" width="100" height="100" style="object-fit:cover;border-radius:4px" />')
        return "No Image"
    image_preview.short_description = "Preview"


class ProductVideosAdminInline(admin.StackedInline):
    model = models.ProductVideos
    fields = ("title", "video", "content_type")
    extra = 1


class ProductAvailableCountriesAdminInline(admin.StackedInline):
    model = models.ProductAvailableCountries
    fields = (("country", "original_price", "selling_price"), "promotion_text")
    extra = 0
    suit_classes = 'suit-tab suit-tab-cities'
    suit_form_inlines_hide_original = True
    min_num = 1


class ProductContentAdminInline(SummernoteInlineModelAdmin, admin.StackedInline):
    model = models.ProductContent
    fields = ("heading", "content")
    extra = 1


class UploadedProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "Uploaded Products"
        verbose_name_plural = "1. Uploaded Products"


class ContentNeededProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "ContentNeeded Products"
        verbose_name_plural = "2. ContentNeeded Products"


class ContentUpdatedProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "Content Updated Products"
        verbose_name_plural = "3. Content Updated Products"


class ReadyPublishProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "Ready to Publish"
        verbose_name_plural = "4. Ready to Publish"


class PublishedProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "Published Publish"
        verbose_name_plural = "5. Published Publish"


class AllProductsProducts(models.Products):
    class Meta:
        proxy = True
        verbose_name = "All Products"
        verbose_name_plural = " All Products"


@admin.register(PublishedProducts, ReadyPublishProducts, ContentUpdatedProducts, ContentNeededProducts,
                UploadedProducts, AllProductsProducts, site=my_admin_site)
class ProductsAdmin(RelatedFieldAdmin):
    list_display = (
        "id",
        "title",
        "sku",
        "category",
        "sub_category",
        "weight",
        "stock_qty",
        "image_tag",
        "status_btn",
        "is_active",
        "ordering",
        "created_on",
    )
    list_filter = ("is_pre_order", "is_active", "design_type",
                   "is_stock", "category", "sub_category", "design")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "sku", "slug")
    change_list_template = "product-import.html"
    filter_horizontal = ("tags",)
    list_select_related = True
    radio_fields = {"status": admin.HORIZONTAL}
    fieldsets = (
        ('Basic info', {
            'classes': ('suit-tab suit-tab-general',),
            'fields': (("sku", 'title'), "slug", "short_descriptions", "weight", ("category", "sub_category"))
        }),
        ("Design", {
            "fields": (("design_type", "design"), "tags")
        }),
        ('Other Info', {
            'classes': ('suit-tab suit-tab-general',),
            'fields': (
                'thumbnail_image', ("support_number",
                                    "financial_year", "stock_qty"),
                ("price_category", "is_active"), "status", "is_stock", "is_barter")
        }),
    )
    suit_form_tabs = (
        ('general', 'General'),
        ('cities', 'Cities'),
    )
    inlines = [ProductAvailableCountriesAdminInline, ProductImagesAdminInline, ProductVideosAdminInline,
               ProductContentAdminInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
            path('download-csv/', self.download_product),
            path('pre-upload-product/', self.pre_upload_product),
            path('add-product/', self.add_product),
            path('publish/', self.publish_products),
            path('delete-all/', self.delete_all_products),
            path('update-status/<int:pk>/<int:status>/', self.update_status),
        ]
        return my_urls + urls

    def download_product(self, request):
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Products.csv'
        fieldnames = ["id", "title", "description", "price", "sale_price", "currency", "condition", "image_link",
                      "additional_image_link", "link", "availability", "google_product_category", "product_type",
                      "color", "material", "size", "gender", "brand", "custom_label_0", "custom_label_1",
                      "custom_label_2", "custom_label_3", "custom_label_4"]
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        for product in models.Products.objects.all():
            currency = ""
            original_price = 0
            sale_price = 0
            image_link = ""
            if product.thumbnail_image:
                image_link = "https://api.spaceandbeauty.com" + product.thumbnail_image.url
            else:
                first_image = product.product_images.first()
                if first_image and first_image.image:
                    image_link = "https://api.spaceandbeauty.com" + first_image.image.url
            link = "https://www.spaceandbeauty.com/in/product/" + product.slug

            price = product.product_country.filter(country__code="INR").first()
            if price:
                currency = price.country.code
                sale_price = price.selling_price
                original_price = price.original_price

            writer.writerow({
                "id": product.sku,
                "title": product.title,
                "description": product.short_descriptions,
                "price": original_price,
                "sale_price": sale_price,
                "currency": currency,
                "image_link": image_link,
                "link": link,
                "product_type": product.category.super_category.title,
                "brand": "Space and Beauty",
            })

        return response

    def get_queryset(self, request):
        qs = super(ProductsAdmin, self).get_queryset(request)
        if self.model.__name__ == "PublishedProducts":
            return qs.filter(status=5)
        elif self.model.__name__ == "ReadyPublishProducts":
            return qs.filter(status=4)
        elif self.model.__name__ == "ContentUpdatedProducts":
            return qs.filter(status=3)
        elif self.model.__name__ == "ContentNeededProducts":
            return qs.filter(status=2)
        elif self.model.__name__ == "UploadedProducts":
            return qs.filter(status=1)
        else:
            return qs

    def status_btn(self, obj):
        text = ""
        status = ""
        if self.model.__name__ == "PublishedProducts":
            return mark_safe("""<span class="badge badge-secondary">{}</span>""".format(obj.get_status_display()))
        elif self.model.__name__ == "AllProductsProducts":
            return mark_safe("""<span class="badge badge-secondary">{}</span>""".format(obj.get_status_display()))
        elif self.model.__name__ == "ReadyPublishProducts":
            text = "Move to Publish"
            status = 5
        elif self.model.__name__ == "ContentUpdatedProducts":
            text = "Ready to Publish"
            status = 4
        elif self.model.__name__ == "ContentNeededProducts":
            text = "Content Verify"
            status = 3
        elif self.model.__name__ == "UploadedProducts":
            text = "Move Content Update"
            status = 2
        return mark_safe(
            """<a class='btn btn-outline-secondary' href=update-status/{id}/{status}/>{text}</a>""".format(
                text=text, status=status, id=obj.id))

    @staticmethod
    def update_status(request, pk, status):
        if not request.user.is_authenticated:
            return redirect('/')
        order = utils.int_to_product(pk)
        order.status = status
        order.save()
        return redirect("../../../")

    @transaction.atomic()
    def pre_upload_product(self, request):
        if not request.user.is_authenticated:
            return redirect('/')
        return render(request, "product-upload.html", {})

    def import_csv(self, request):
        if request.method == "POST":
            if request.FILES["csv_file"].name.endswith(".csv"):
                csv_file = request.FILES["csv_file"]
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    super_category = SuperCategories.objects.get(
                        title=row['Super Category'].strip())

                    category, _ = Categories.objects.get_or_create(title=row['Category'].strip(),
                                                                   super_category=super_category,
                                                                   defaults={
                                                                       "title": row['Category'].strip(),
                                                                       "super_category": super_category,
                                                                       "code": row['Category'].strip()[:3]
                    })

                    sub_ca, _ = models.SubCategories.objects.get_or_create(category=category,
                                                                           title=row['Sub-category'].strip(
                                                                           ),
                                                                           defaults={
                                                                               "category": category,
                                                                               "title": row['Sub-category'].strip(),
                                                                               "code": row['Sub-category'].strip()[:3]
                                                                           })

                    design_type, _ = models.DesignType.objects.get_or_create(title=row['Type'].strip(), defaults={
                        "slug": slugify(row['Type'].strip()),
                        "title": row['Type'].strip()
                    })
                    design, _ = models.ProductDesign.objects.get_or_create(code=row['Design Code'], defaults={
                        "code": row['Design Code'].strip(),
                        "title": row['Design Name'].strip()
                    })

                    title = "{} {} {}".format(
                        category, sub_ca, row['SKU'].strip())
                    slug = slugify(title)
                    thumbnail_image = "product/product-image/{}".format(
                        row['Product Image'])

                    product_dict = {
                        "sku": row['SKU'].strip(),
                        "title": row['Title'],
                        "slug": slug,
                        "bt_code": row.get("Code", None),
                        "short_descriptions": row.get("One Liner", None),
                        "category": category,
                        "sub_category": sub_ca,
                        "thumbnail_image": thumbnail_image,
                        "support_number": row['Support Number'],
                        "stock_qty": row['Stock(QTY)'].strip(),
                        "design_type": design_type,
                        "design": design,
                        "financial_year": row.get('Financial Year', datetime.year),
                        "price_category_id": 1 if row['Pricing Category'] == "A" else 2,
                    }
                    product = get_object_or_None(
                        models.Products, sku=product_dict['sku'])

                    if product:
                        product_dict.pop("sku")
                        product.__dict__.update(**product_dict)
                    else:
                        print(product_dict['sku'])
                        product = models.Products.objects.create(
                            **product_dict)

                        for image in row['Other Images'].split(","):
                            if image:
                                image_url = "product/product-image/{}".format(
                                    image)
                                models.ProductImages.objects.create(product=product, title=product.title,
                                                                    image=image_url)

                        if row['Description']:
                            models.ProductContent.objects.create(product=product, heading="Description",
                                                                 content=row['Description'])

                        country = models.Countries.objects.get(id=1)
                        models.ProductAvailableCountries.objects.create(country=country, product=product,
                                                                        original_price=row['Cost Price'],
                                                                        selling_price=row['Selling Price'])

                self.message_user(request, "Your csv file has been imported")
                return redirect("..")

        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "csv_form.html", payload)

    def add_product(self, request):
        if not request.user.is_authenticated:
            return redirect('/')
        return render(request, "product-upload.html", {})

    def publish_products(self, request):
        if not request.user.is_authenticated:
            return redirect('/')
        qs = self.get_queryset(request)
        count = qs.update(status=5)
        self.message_user(
            request, "{} product(s) published successfully.".format(count))
        return redirect("../")

    def delete_all_products(self, request):
        if not request.user.is_authenticated:
            return redirect('/')
        qs = self.get_queryset(request)
        count = qs.count()
        qs.delete()
        self.message_user(
            request, "{} product(s) deleted successfully.".format(count))
        return redirect("../")

    def has_delete_permission(self, request, obj=None):
        return False

from datetime import datetime

from django.db import transaction
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, filters, response, generics, exceptions
from rest_framework.decorators import action, api_view

from categories.models import Categories
from categories.serializers import CategoriesSerializers, SubCategoriesSerializers, ChildSubCategoriesSerializers, \
    ChildSuperCategoriesSerializer, ChildCategoriesSerializers, TitleSerializers
from categories.utils import int_to_super_category, int_to_category, int_to_sub_categories
from space_and_beauty.pagination import RestFrameworkPaginationMixin
from . import serializers, models, utils
from .filters import ProductsFilter


class ProductsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    use this endpoint do following operations
    1. List Products with pagination
    2. List Specific Products
    """
    serializer_class = serializers.ProductsSerializers
    model = models.Products
    pagination_class = RestFrameworkPaginationMixin
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ("sub_category__title",)
    filter_class = ProductsFilter
    lookup_field = 'slug'

    def get_serializer_class(self):
        if "slug" in self.kwargs:
            return serializers.ProductsSerializers
        return serializers.ListProductSerializers

    def get_queryset(self):
        filter_dict = {}
        return self.model.objects.filter(status=5, is_active=True, **filter_dict).annotate(
            price=Max('product_country__selling_price')).order_by("-is_stock", "price")

    @action(detail=False)
    def home_products(self, request):
        # Get the first 6 active products for homepage
        products = models.Products.objects.filter(status=5, is_active=True).order_by('id')[:6]
        serializer = serializers.ProductsSerializers(products, many=True, context={"request": request}).data
        return response.Response(serializer)

    # hero_featured endpoint removed (field is no longer used)

    @action(detail=False)
    def home_category(self, request):
        categories = Categories.objects.filter(id__in=[3], is_active=True)
        serializer = CategoriesSerializers(categories, many=True,
                                           context={"request": request}).data
        return response.Response(serializer)

    @action(detail=True)
    def similar_products(self, request, slug):
        product = utils.slug_to_product(slug)
        products = models.Products.objects.filter(category=product.category, status=5).order_by("?")[:8]
        serializer = serializers.ListProductSerializers(products, many=True, context={"request": request}).data
        return response.Response(serializer)

    @action(detail=False, methods=['POST'])
    def track_view(self, request):
        product_id = request.data.get('product_id')
        if product_id:
            try:
                product = models.Products.objects.get(id=product_id)
                # You can add tracking logic here (e.g., increment view count)
                # For now, just return success
                return response.Response({"status": "success", "message": "View tracked"})
            except models.Products.DoesNotExist:
                return response.Response({"status": "error", "message": "Product not found"}, status=404)
        return response.Response({"status": "error", "message": "Product ID required"}, status=400)

    @action(detail=False, methods=['GET'])
    def category_filter(self, request):
        data = dict()
        filter_dict = {}
        query_flag = False
        filter_query = [{"key": "sub_category", "field_name": "sub_category"},
                        {"key": "category", "field_name": "category"},
                        {"key": "super_category", "field_name": "category__super_category"}]

        for field in filter_query:
            if field['key'] in request.query_params and request.query_params[field['key']]:
                filter_dict[field['field_name']] = request.query_params[field['key']]
                query_flag = True

        for field in filter_query:
            if field['key'] in request.query_params and request.query_params[field['key']]:
                if field['key'] == "sub_category":
                    filter_obj = int_to_sub_categories(request.query_params[field['key']])
                    data['sub_category'] = ChildSubCategoriesSerializers(filter_obj, context={"request": request}).data
                    break

                elif field['key'] == "category":
                    filter_obj = int_to_category(request.query_params[field['key']])
                    data['category'] = ChildCategoriesSerializers(filter_obj, context={"request": request}).data
                    break

                elif field['key'] == "super_category":
                    filter_obj = int_to_super_category(request.query_params[field['key']])
                    data['super_category'] = ChildSuperCategoriesSerializer(filter_obj,
                                                                            context={"request": request}).data

        if query_flag:
            design_type = self.get_queryset().filter(**filter_dict).values("design_type", 'category',
                                                                           "category__super_category",
                                                                           "sub_category").distinct()
            design_obj = models.DesignType.objects.filter(id__in=[x['design_type'] for x in design_type])

            data['filter'] = [{
                "title": "Product Type",
                "filter_key": "design_type",
                "data": TitleSerializers(design_obj, many=True, context={"request": request}).data
            }]

            categories = models.Categories.objects.filter(
                super_category__in=[x['category__super_category'] for x in design_type], is_active=True)
            data['filter'].append({
                "title": "Collections",
                "filter_key": "category",
                "data": TitleSerializers(categories, many=True, context={"request": request}).data})

            sub_category = models.SubCategories.objects.filter(id__in=[x['sub_category'] for x in design_type],
                                                               is_active=True)
            data['filter'].append({
                "title": "Models",
                "filter_key": "sub_category",
                "data": TitleSerializers(sub_category, many=True, context={"request": request}).data})

            tags = models.ProductTags.objects.filter(is_active=True)

            data['filter'].append({
                "title": "Tags",
                "filter_key": "tags",
                "data": TitleSerializers(tags, many=True, context={"request": request}).data})

        else:
            data['filter'] = []

        return response.Response(data)


class ProductsByIdsView(generics.GenericAPIView):
    """
    Fetch products by IDs for cart/add-to-cart flow from homepage sections.
    GET /products/by_ids/?ids=1,2,3
    """
    serializer_class = serializers.ProductsSerializers

    def get(self, request):
        ids_param = request.query_params.get('ids', '')
        if not ids_param:
            return response.Response([])
        try:
            ids = [int(x.strip()) for x in ids_param.split(',') if x.strip()]
        except ValueError:
            return response.Response([])
        products = models.Products.objects.filter(id__in=ids, is_active=True, status=5)
        serializer = self.get_serializer(products, many=True)
        return response.Response(serializer.data)


class ProductUploadView(generics.GenericAPIView):
    """
    use this endpoint do following operations
    1. Upload products and generate SKU for corresponding Product
    """

    @transaction.atomic()
    def post(self, request):
        serializer = serializers.UploadProductSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)
        product_dict = {
            "stock_qty": serializer.data['stock_qty'],
            "support_number": "9791311511",
            "financial_year": datetime.today().year,
            "thumbnail_image": request.FILES['product_image'],
            "price_category_id": serializer.data['pricing_category'],
            "short_descriptions": "Need to Add",
            "slug": "need-to-add",
            "title": "need-to-add",
            "sub_category_id": serializer.data['sub_category'],
            "is_barter": False,
            "is_pre_order": False,
            "is_barter_order_count": 5,
            "affiliate_percentage": 5,
        }

        product = models.Products.objects.create(**product_dict)

        country = models.Countries.objects.get(id=1)
        models.ProductAvailableCountries.objects.create(country=country, product=product,
                                                        original_price=serializer.data['original_price'],
                                                        selling_price=serializer.data['offer_price'])

        return response.Response(serializers.ProductsSerializers(product, context={"request": self.request}).data)

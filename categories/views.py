from rest_framework import response, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.views import APIView

from affiliate_management.models import PaymentType
from . import models, serializers


class MasterCategoriesViewSet(viewsets.GenericViewSet):
    """
    use this endpoint do list the master values
    1. Category and sub-categories
    2. Country list
    """

    def list(self, request):
        data = dict()
        categories = models.SuperCategories.objects.filter(
            id__in=[1, 2, 3, 4, 5], is_active=True).order_by("ordering")
        data['category'] = serializers.LimitSuperCategoriesSerializer(categories, many=True,
                                                                      context={"request": request}).data

        countries = models.Countries.objects.filter(is_active=True)
        data['countries'] = serializers.CountriesSerializers(countries, many=True,
                                                             context={"request": request}).data

        payment_type = PaymentType.objects.all()
        data['payment_type'] = serializers.NameSerializers(payment_type, many=True,
                                                           context={"request": request}).data

        pricing_category = models.PricingCategories.objects.all()
        data['pricing_category'] = serializers.TitleSerializers(pricing_category, many=True,
                                                                context={"request": request}).data

        return response.Response(data)

    @action(detail=True, methods=['GET'])
    def category_tags(self, request, pk):
        tags = models.ProductTags.objects.filter(category=pk, is_active=True)
        serializer = serializers.ProductTagsSerializer(
            tags, many=True, context={"request": request}).data

        return response.Response(serializer)


class HomepageSectionView(APIView):
    def get(self, request):
        sections = models.HomepageSection.objects.filter(
            is_active=True).exclude(section_type='hero').order_by('ordering')
        serializer = serializers.HomepageSectionSerializer(
            sections, many=True, context={'request': request})
        return response.Response(serializer.data)


class HeroBannerView(APIView):
    def get(self, request):
        banners = models.HeroBanner.objects.filter(
            is_active=True).order_by('ordering')
        serializer = serializers.HeroBannerSerializer(
            banners, many=True, context={'request': request})
        return response.Response(serializer.data)


class CountriesView(APIView):
    """
    Get all active countries with flags and currency
    """

    def get(self, request):
        countries = models.Countries.objects.filter(
            is_active=True).order_by('title')
        serializer = serializers.CountriesSerializers(
            countries, many=True, context={'request': request})
        return response.Response(serializer.data)


class CategoriesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    use this endpoint to do following operations
    1. List Categories details
    """
    model = models.SuperCategories
    serializer_class = serializers.LimitSuperCategoriesSerializer

    def get_queryset(self):
        return self.model.objects.filter(is_active=True)

from django_filters import rest_framework as filters, Filter

from . import models


class M2MFilter(Filter):

    def filter(self, qs, value):
        filter_query = {}
        if not value:
            return qs
        values = value.split(',')
        new_key = self.field_name + '__in'
        filter_query[new_key] = [x for x in values if x]
        queryset = qs.filter(**filter_query)
        return queryset.distinct()


class ProductsFilter(filters.FilterSet):
    tags = M2MFilter(field_name="tags")
    category = M2MFilter(field_name="category")
    sub_category = M2MFilter(field_name="sub_category")
    super_category = M2MFilter(field_name="category__super_category")
    price_category = M2MFilter(field_name="price_category")
    design_type = M2MFilter(field_name="design_type")

    class Meta:
        model = models.Products
        fields = ["sku", "price_category", "tags", "category", "sub_category", "design_type", "super_category"]

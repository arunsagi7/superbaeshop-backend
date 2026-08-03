from itertools import chain
from urllib.parse import urlencode
from django.db.models import F, Max


from django.contrib.sites.shortcuts import get_current_site
from rest_framework import exceptions
from rest_framework.pagination import LimitOffsetPagination


class RestFrameworkPaginationMixin(LimitOffsetPagination):
    default_limit = 10
    max_limit = 52
    limit_query_param = "limit"
    offset_query_param = "offset"


class PaginationMixin(object):
    def __init__(self):
        self.page_max_size = None
        self.request = None

    def get_pagination_response(self, qs):
        query_count = qs + """.count()"""
        count = eval(query_count)
        url = ('https' if self.request.is_secure() else 'http') + "://" + get_current_site(
            self.request).name + self.request.path
        kwargs = self.request.query_params.dict()
        if 'page' in kwargs:
            try:
                page = int(kwargs['page'])
                del (kwargs['page'])
            except:
                raise exceptions.ValidationError({'page': ['page is not a valid integer.']})
        else:
            page = 1
        end = page * self.page_max_size
        start = end - self.page_max_size
        qs += """[{}:{}]""".format(start, end)
        queryset = eval(qs)
        kw = urlencode(kwargs, doseq=True)
        prev_page = page - 1
        next_page = page + 1
        if kwargs:
            amber = '&'
        else:
            amber = ''
        if int(page) == 1 or page > (count / self.page_max_size) + 1:
            prev_url = None
        else:
            prev_url = url + '?' + kw + amber + "page=%s" % str(prev_page)
        if int(end) >= count:
            next_url = None
        else:
            next_url = url + '?' + kw + amber + "page=%s" % str(next_page)
        return count, prev_url, next_url, queryset

    def get_search_pagination_response(self, qs1, qs2):
        query_count = eval(qs2 + """.count()""")
        qs1_count = eval(qs1 + """.count()""")
        count = query_count + qs1_count
        url = ('https' if self.request.is_secure() else 'http') + "://" + get_current_site(self.request
                                                                                           ).name + self.request.path
        kwargs = self.request.query_params.dict()
        if 'page' in kwargs:
            try:
                page = int(kwargs['page'])
                del (kwargs['page'])
            except:
                raise exceptions.ValidationError({'page': ['page is not a valid integer.']})
        else:
            page = 1

        end = page * self.page_max_size
        start = end - self.page_max_size
        if end > qs1_count != 0:
            balance = end - qs1_count
            if balance < self.page_max_size and balance != 0:
                qs1 += """[{}:{}]""".format(start, end)
                qs2 += """[0:{}]""".format(balance)
                queryset = list(chain(eval(qs1), eval(qs2)))
            else:
                qs2 += """[{}:{}]""".format((start - qs1_count), (end - qs1_count))
                queryset = eval(qs2)

        elif qs1_count == 0:
            queryset = eval(qs2 + """[{}:{}]""".format(start, end))
        else:
            queryset = eval(qs1 + """[{}:{}]""".format(start, end))

        kw = urlencode(kwargs, doseq=True)
        prev_page = page - 1
        next_page = page + 1
        if kwargs:
            amber = '&'
        else:
            amber = ''
        if int(page) == 1 or page > (count / self.page_max_size) + 1:
            prev_url = None
        else:
            prev_url = url + '?' + kw + amber + "page=%s" % str(prev_page)
        if int(end) >= count:
            next_url = None
        else:
            next_url = url + '?' + kw + amber + "page=%s" % str(next_page)
        return count, prev_url, next_url, queryset

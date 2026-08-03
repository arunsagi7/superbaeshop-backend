from django.contrib import admin

from authentication.utils import SendOneTimePassword
from categories.admin import my_admin_site
from tokens_management import models


@admin.register(models.TokenState, models.TokenType, site=my_admin_site)
class NameAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    def has_delete_permission(self, request, obj=None):
        return False


class TokenHistoryAdmin(admin.StackedInline):
    model = models.TokenHistory
    fields = ("comment",)


class NewTokens(models.Token):
    class Meta:
        proxy = True
        verbose_name = "New Tokens"
        verbose_name_plural = "1. New Tokens"


class ResolvedTokens(models.Token):
    class Meta:
        proxy = True
        verbose_name = "Resolved Tokens"
        verbose_name_plural = "2. Resolved Tokens"


@admin.register(NewTokens, ResolvedTokens, site=my_admin_site)
class TokenAdmin(admin.ModelAdmin, SendOneTimePassword):
    list_display = ("id", "token_id", "order", "token_type", "token_state", "token_description", "is_solved",
                    "created_on")
    inlines = [TokenHistoryAdmin]
    date_hierarchy = "created_on"
    readonly_fields = ("token_id",)
    search_fields = ("token_id",)
    list_filter = ("token_state", "token_type")

    def get_queryset(self, request):
        qs = super(TokenAdmin, self).get_queryset(request)
        name = self.model.__name__
        if name == "NewTokens":
            return qs.filter(is_solved=False)
        elif name == "ResolvedTokens":
            return qs.filter(is_solved=True)
        else:
            return qs

    def has_delete_permission(self, request, obj=None):
        return False

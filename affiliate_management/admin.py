from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

from affiliate_management import models
from categories.admin import my_admin_site


@admin.register(models.WalletHistory, site=my_admin_site)
class WalletHistoryAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "is_credit", 'created_on')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        return False


@admin.register(models.PaymentType, site=my_admin_site)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    def has_delete_permission(self, request, obj=None):
        return False


class AffiliatesForm(forms.ModelForm):
    name = forms.CharField()
    email = forms.EmailField()
    paid_amount = forms.IntegerField(required=False)
    phone = forms.CharField(max_length=12, widget=forms.NumberInput())
    model = models.Affiliates

    def clean_phone(self):
        if models.User.objects.filter(username=self.cleaned_data['phone']).exclude(
                username=self.instance.user.username if self.instance.pk else ""):
            raise ValidationError('Phone Number already exists')
        return self.cleaned_data['phone']


@admin.register(models.Affiliates, site=my_admin_site)
class AffiliatesAdmin(admin.ModelAdmin):
    list_display = ("created_on", "name", "email", "phone", "offer", "payment_type",
                    "is_active", "purchase", "otp", "wallet_amount", "total_paid", "total_amount", "view_history")
    list_filter = ("is_active",)
    form = AffiliatesForm
    date_hierarchy = "created_on"
    search_fields = ("user__first_name", "user__username", "user__email", "user__last_name", "referral_code",
                     "offer__offer_code")

    fieldsets = (
        ("", {
            "fields": ("name", "email", ("phone_code", "phone"), "payment_type", "payment_details",
                       "social_media", "paid_amount",)
        }),
        ("Address", {
            "fields": ("door_no", "street_address", "city", "state", "country", "postal_code")
        }),
        ("Active", {
            "fields": ("is_active",)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:
            user = models.User.objects.create_user(username=form.cleaned_data['phone'],
                                                   first_name=form.cleaned_data['name'],
                                                   email=form.cleaned_data['email'],
                                                   password="spacebeauty", is_active=True)
            obj.user = user

        else:
            obj.user.username = form.cleaned_data['phone']
            obj.user.first_name = form.cleaned_data['name']
            obj.user.email = form.cleaned_data['email']

            if form.cleaned_data.get("paid_amount"):
                obj.wallet_amount = round(obj.wallet_amount - form.cleaned_data.get("paid_amount", 0))
                obj.total_paid = round(obj.total_paid + form.cleaned_data.get("paid_amount", 0))

        super(AffiliatesAdmin, self).save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super(AffiliatesAdmin, self).get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['phone'].initial = obj.user.username
            form.base_fields['name'].initial = obj.user.first_name
            form.base_fields['email'].initial = obj.user.email

        return form

    def view_history(self, obj):
        return mark_safe("""<a class='btn btn-outline-secondary' 
        href='/affiliate_management/wallethistory/?user__id={id}'> View History</a>""".format(id=obj.id))

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def name(affiliate):
        return affiliate.user.get_full_name()

    @staticmethod
    def email(affiliate):
        return affiliate.user.email

    @staticmethod
    def phone(affiliate):
        return affiliate.user.username

    @staticmethod
    def purchase(affiliate):
        return 0

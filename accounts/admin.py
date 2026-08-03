import csv

from annoying.functions import get_object_or_None
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.timezone import now

from accounts import models
from categories.admin import my_admin_site
from orders_management.models import Orders


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

    def clean(self):
        if not (self.cleaned_data['csv_file'] or self.cleaned_data['csv_file'].endswith(".csv")):
            raise forms.ValidationError(
                'Please enter your code in text box or upload an appropriate file.')
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    name = forms.CharField(required=False)
    email = forms.EmailField()
    is_active = forms.BooleanField()
    add_wallet_points = forms.IntegerField(required=False)
    phone = forms.CharField(max_length=12, widget=forms.NumberInput())
    model = models.User

    def clean_phone(self):
        if models.User.objects.filter(username=self.cleaned_data['phone']).exclude(
                username=self.instance.user.username if self.instance.pk else ""):
            raise ValidationError('Phone Number already exists')
        return self.cleaned_data['phone']

    def clean_email(self):
        if models.User.objects.filter(email=self.cleaned_data['email']).exclude(
                email=self.instance.user.email if self.instance.pk else ""):
            raise ValidationError('Email Id already exists')

        return self.cleaned_data['email']


class UserPointsHistoryAdminInline(admin.StackedInline):
    model = models.UserPointsHistory
    fields = ("point", "pre_point", "is_credit", "created_on")
    readonly_fields = ("created_on",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class AddressAdminInline(admin.StackedInline):
    model = models.Address
    fields = ("door_no", "street_address", "city", "locality", "landmark", "address_type", "state",
              "country", "postal_code", "is_active")

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.UserProfile, site=my_admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("date_joined", "name", "email", "mobile",
                    "user_points", "is_active", "otp")
    list_display_links = ("date_joined", "name", "email",
                          "mobile", "user_points", "is_active", "otp")
    inlines = [AddressAdminInline, UserPointsHistoryAdminInline]
    form = UserProfileForm
    search_fields = ("user__first_name", "user__username", "user__email")
    readonly_fields = ("user_points", "used_points", "total_points")

    change_list_template = "user_list_template.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('download-csv/', self.download_users),
        ]
        return my_urls + urls

    fieldsets = (
        ('Basic info', {
            'fields': (("name", "email", "phone"),)
        }),
        ('Other info', {
            'fields': ('profile_pic', "country", "add_wallet_points", ("user_points", "used_points", "total_points"),
                       "is_active")
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    @staticmethod
    def name(profile):
        return profile.user.get_full_name()

    @staticmethod
    def email(profile):
        return profile.user.email

    @staticmethod
    def mobile(profile):
        return profile.user.username

    @staticmethod
    def date_joined(profile):
        return profile.user.date_joined.date()

    @staticmethod
    def is_active(profile):
        return profile.user.is_active

    def save_model(self, request, obj, form, change):
        if not change:
            user = models.User.objects.create_user(username=form.cleaned_data['phone'],
                                                   first_name=form.cleaned_data.get(
                                                       'name', ""),
                                                   email=form.cleaned_data['email'],
                                                   is_active=True)
            obj.user = user
        else:
            obj.user.username = form.cleaned_data.get(
                'phone', obj.user.username)
            obj.user.first_name = form.cleaned_data.get(
                'name', obj.user.first_name)
            obj.user.email = form.cleaned_data.get('email', obj.user.email)
            obj.user.is_active = form.cleaned_data.get(
                'is_active', obj.user.is_active)
            obj.user.save()
            if form.cleaned_data.get("add_wallet_points"):
                obj.user_points += form.cleaned_data.get(
                    "add_wallet_points", 0)
                obj.total_points += form.cleaned_data.get(
                    "add_wallet_points", 0)

        super(UserProfileAdmin, self).save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super(UserProfileAdmin, self).get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['phone'].initial = obj.user.username
            form.base_fields['name'].initial = obj.user.first_name
            form.base_fields['email'].initial = obj.user.email
            form.base_fields['is_active'].initial = obj.user.is_active

        else:
            form.base_fields['phone'].initial = ""
            form.base_fields['name'].initial = ""
            form.base_fields['email'].initial = ""

        return form

    def import_csv(self, request, ):
        if request.method == "POST":
            if request.FILES["csv_file"].name.endswith(".csv"):
                csv_file = request.FILES["csv_file"]
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                country = models.Countries.objects.first()
                for row in reader:

                    user = get_object_or_None(
                        models.User, username=row['Phone'])
                    if user:
                        user.userprofile.user_points = 500
                        user.userprofile.total_points = 500
                        user.userprofile.save()
                    print(user)
                self.message_user(request, "Your csv file has been imported")
                return redirect("..")

        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "csv_form.html", payload)

    @staticmethod
    def download_users(request):

        if not request.user.is_authenticated:
            return redirect('/')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Cart-{}.csv'.format(
            now().date())
        writer = csv.writer(response)
        writer.writerow(("Name", "Email", "Phone", "is_order"))

        queryset = models.UserProfile.objects.filter()

        for obj in queryset:
            is_order = "True" if Orders.objects.filter(
                user=obj, is_success=True) else "False"
            row_list = [obj.user.first_name,
                        obj.user.email, obj.user.username, is_order]
            writer.writerow(row_list)

        return response

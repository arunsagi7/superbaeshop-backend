from django.contrib.auth.models import User
from django.db import models

from categories.models import Countries
from django.utils.translation import gettext_lazy as _

ADDRESS_TYPE_CHOICES = (
    ("Home", _("Home")),
    ("Work", _("Work"))
)

GENDER_CHOICES = (
    ("Male", _("Male")),
    ("Female", _("Female"))
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to="profile_pic", blank=True, null=True)
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, blank=True, null=True)
    user_points = models.IntegerField(default=0, verbose_name="Available Points")
    used_points = models.IntegerField(default=0, verbose_name="Total User Points")
    total_points = models.IntegerField(default=0, verbose_name="Total Earned Points")
    otp = models.PositiveIntegerField(blank=True, null=True)
    otp_expired = models.DateTimeField(blank=True, null=True)
    country = models.ForeignKey(Countries, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = "tbl_userprofile"
        verbose_name = "UserProfile"
        verbose_name_plural = "UserProfile"

    def __str__(self):
        return "{}".format(self.user.get_full_name())


class Address(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_address")
    door_no = models.CharField(max_length=50)
    street_address = models.CharField(max_length=256)
    city = models.CharField(max_length=256)
    state = models.CharField(max_length=120)
    locality = models.CharField(max_length=256)
    landmark = models.CharField(max_length=256, blank=True, null=True)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, verbose_name="Address Type")
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_user_address"
        verbose_name = "Address"
        verbose_name_plural = "Address"

    def __str__(self):
        return "{}".format(self.user)


class UserPointsHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_points_history")
    point = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    pre_point = models.DecimalField(default=0, decimal_places=2, max_digits=15)
    is_credit = models.BooleanField()
    description = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_user_points_history"
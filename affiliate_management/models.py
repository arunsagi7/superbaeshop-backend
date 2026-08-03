from django.contrib.auth.models import User
from django.db import models

from categories.models import Countries
from offers_management.models import Coupon


class PaymentType(models.Model):
    objects = None
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "tbl_affiliate_payment_type"
        verbose_name = "Payment Type"
        verbose_name_plural = "2. Payment Type"

    def __str__(self):
        return self.name


class Affiliates(models.Model):
    objects = None
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_code = models.ForeignKey(Countries, on_delete=models.CASCADE, related_name="country_code")
    door_no = models.CharField(max_length=50)
    street_address = models.CharField(max_length=256)
    city = models.CharField(max_length=256)
    state = models.CharField(max_length=256)
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=10)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    payment_details = models.TextField()
    offer = models.OneToOneField(Coupon, on_delete=models.CASCADE, blank=True, null=True,
                                 related_name="affiliate_offer")
    otp = models.PositiveIntegerField(blank=True, null=True)
    otp_expired = models.DateTimeField(blank=True, null=True)
    is_otp_verify = models.BooleanField(default=False)
    social_media = models.CharField(max_length=256, blank=True, null=True, help_text="Eg: Fb link, Insta, etc")
    referral_code = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    wallet_amount = models.FloatField(default=0)
    total_paid = models.IntegerField(default=0)
    total_amount = models.FloatField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_affiliates"
        verbose_name = "Affiliate"
        verbose_name_plural = "1. Affiliates"

    def __str__(self):
        return self.user.get_full_name()


class AffiliatesReferral(models.Model):
    objects = None
    referred_by = models.ForeignKey(Affiliates, on_delete=models.CASCADE, related_name="referred_by")
    referral = models.ForeignKey(Affiliates, on_delete=models.CASCADE, related_name="referral_user")

    class Meta:
        db_table = "tbl_affiliates_referral"
        verbose_name = "Affiliate Referral"
        verbose_name_plural = "Affiliates Referrals"
        unique_together = ("referred_by", "referral")


class WalletHistory(models.Model):
    objects = None
    user = models.ForeignKey(Affiliates, on_delete=models.CASCADE, related_name="wallet")
    description = models.CharField(max_length=255)
    amount = models.FloatField(default=0)
    currency = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True)
    is_credit = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_wallet_history"

    def __str__(self):
        return self.description

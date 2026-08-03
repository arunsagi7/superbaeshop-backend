from django.core.validators import MinValueValidator
from django.db import models

from accounts.models import Address, UserProfile
from affiliate_management.models import Affiliates
from categories.models import Countries, PaymentGateWay
from offers_management.models import Coupon
from product_management.models import Products

PAYMENT_TYPE_CHOICES = (
    ("Online", "Online"),
    ("COD", "Cash On Delivery"),
)


class OrderStatusMaster(models.Model):
    objects = None
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "tbl_order_status_master"
        verbose_name = "Order Status"
        verbose_name_plural = "Order Status"


class OrderStatus(models.Model):
    objects = None
    order_status = models.ForeignKey(OrderStatusMaster, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_order_status"
        verbose_name = "Order Status"
        verbose_name_plural = "Order Status"

    def __str__(self):
        return self.name


class Orders(models.Model):
    objects = None
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="my_orders")
    tracking_client_id = models.CharField(max_length=40, blank=True, editable=False, unique=True,
                                          verbose_name="Tracking ID")
    awb_code = models.CharField(max_length=60, blank=True, null=True)
    track_url = models.CharField(max_length=120, blank=True, null=True)
    transaction_id = models.CharField(max_length=120, unique=True, blank=True, null=True)
    payment_id = models.CharField(max_length=256, blank=True, null=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=12)
    alt_phone = models.CharField(max_length=12, blank=True, null=True)
    dial_code = models.CharField(max_length=5)
    alt_dial_code = models.CharField(max_length=5, blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    is_wallet = models.BooleanField(default=False)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE, default=1)
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    currency_type = models.CharField(max_length=12)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, related_name="user_offer")
    coupon_code = models.CharField(max_length=20, blank=True, null=True)
    payment_gateway = models.ForeignKey(PaymentGateWay, on_delete=models.SET_NULL, null=True, blank=True)
    pay_mode = models.ForeignKey(PaymentGateWay, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="pay_mode", verbose_name="Pay Mode")
    refund_amount = models.FloatField(default=0)
    is_amount_refunded = models.NullBooleanField(default=None)
    total_amount = models.FloatField(default=0, )
    coupon_amount = models.FloatField(default=0, )
    pay_amount = models.FloatField(default=0, )
    shipping_charge = models.FloatField(default=0, )
    cod_charge = models.FloatField(default=0, )
    other_charge = models.FloatField(default=0, )
    total_gst = models.FloatField(default=0, )
    payment_status = models.BooleanField(default=False)
    is_success = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_orders"
        verbose_name = "Orders"
        verbose_name_plural = "Orders"

    def sub_total_amount(self):
        return round(self.total_amount - (self.other_charge + self.cod_charge + self.shipping_charge + self.total_gst),
                     2)

    def __str__(self):
        return "{}-{}-{}".format(self.tracking_client_id, self.user.user, self.user.user.first_name)

    def discount_amount(self):
        amount = 0
        for item in self.order_items.all():
            amount += item.offer_amount
        return amount


class OrderItems(models.Model):
    objects = None
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="product_order")
    product_sku = models.CharField(max_length=50)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    offer_title = models.CharField(max_length=120, blank=True, null=True)
    offer_amount = models.FloatField(default=0.0)
    currency = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True)
    unit_price = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    color = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        db_table = "tbl_order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def pay_amount(self):
        return round((self.unit_price * self.quantity) - self.offer_amount, 2)


class OrderItemsCancelled(models.Model):
    objects = None
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="order_items_cancelled")
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    product_sku = models.CharField(max_length=50)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    offer_title = models.CharField(max_length=120, blank=True, null=True)
    offer_amount = models.FloatField(default=0.0)
    currency = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True)
    unit_price = models.FloatField(default=0)
    gst = models.FloatField(default=0)
    color = models.CharField(max_length=120, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_order_items_cancellation"

    def pay_amount(self):
        return round((self.unit_price * self.quantity) - self.offer_amount, 2)


class InfluencerOrder(models.Model):
    objects = None
    affiliates = models.ForeignKey(Affiliates, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE, default=1)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_influencer_order"
        verbose_name = "Influencer Order"
        verbose_name_plural = "Influencer Order"

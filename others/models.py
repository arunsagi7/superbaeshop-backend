from django.db import models


class Newsletters(models.Model):
    objects = None
    email = models.EmailField(unique=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_newsletters"
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"

    def __str__(self):
        return self.email


class MasterHtml(models.Model):
    objects = None
    title = models.CharField(max_length=120, unique=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_master_html"
        verbose_name = "Master HTML"
        verbose_name_plural = "Master Html"

    def __str__(self):
        return self.title


class ShipmentLogin(models.Model):
    objects = None
    name = models.CharField(max_length=60)
    username = models.CharField(max_length=120)
    password = models.CharField(max_length=120)
    token = models.TextField(max_length=500)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_shipment_login"
        verbose_name = "Shipment Login"
        verbose_name_plural = "Shipment Login"

    def __str__(self):
        return self.name

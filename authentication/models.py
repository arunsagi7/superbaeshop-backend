from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Token(models.Model):
    objects = None
    key = models.CharField(max_length=40, primary_key=True, help_text=_('User Identification Key'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_tokens')
    client = models.CharField(max_length=255, help_text=_("Unique identify system id"))
    device_token = models.TextField(blank=True, null=True, help_text=_("For Push Notification Device id"))
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_auth_token"
        unique_together = ('user', 'client')
        verbose_name = "Token"
        verbose_name_plural = "Tokens"

from django.db import models

from authentication.utils import SendOneTimePassword
from orders_management.models import Orders


class TokenState(models.Model):
    objects = None
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "tbl_token_state"
        verbose_name = "Token State"
        verbose_name_plural = "Token States"

    def __str__(self):
        return self.name


class TokenType(models.Model):
    objects = None
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "tbl_token_type"
        verbose_name = "Token Type"
        verbose_name_plural = "3. Token Type"

    def __str__(self):
        return self.name


class Token(models.Model):
    objects = None
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    token_id = models.CharField(max_length=12, unique=True)
    token_type = models.ForeignKey(TokenType, on_delete=models.CASCADE)
    token_state = models.ForeignKey(TokenState, on_delete=models.CASCADE)
    token_description = models.TextField()
    is_solved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_tokens"
        verbose_name = "Token"
        verbose_name_plural = "1. Tokens"

    def __str__(self):
        return self.token_id

    def save(self, *args, **kwargs):
        sms = SendOneTimePassword()
        sms.sms_context = {"token": self}
        if not self.token_id:
            sku = self.__class__.objects.latest("id").id if self.__class__.objects.last() else 0
            self.token_id = "ISU{}".format('{0:04}'.format(sku + 1))

            sms.sms_template = "token_create_sms.txt"
            sms.send_verification_otp(self.order.user.user)

            sms.sms_template = "token_create_to_developer.txt"
            sms.send_verification_otp(self.order.user.user, mobile_number="9715868154")
        else:
            if self.is_solved:
                sms.sms_template = "token_resolved_sms.txt"
                sms.send_verification_otp(self.order.user.user)

        super(Token, self).save(*args, **kwargs)


class TokenHistory(models.Model):
    objects = None
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_token_history"
        verbose_name = "Token History"
        verbose_name_plural = "1. Token History"

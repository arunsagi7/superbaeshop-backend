from rest_framework import authentication

from .models import Token


class TokenAuthentication(authentication.TokenAuthentication):
    model = Token


from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


def get(key, role):
    defaults = {
        'SEND_ACTIVATION_EMAIL': False,
        'SET_PASSWORD_RETYPE': False,
        'SET_USERNAME_RETYPE': False,
        'PASSWORD_RESET_CONFIRM_RETYPE': False,
        'ROOT_VIEW_URLS_MAPPING': {},
    }
    if role in [1, 2]:
        defaults.update(getattr(settings, 'ADMIN', {}))
    else:
        defaults.update(getattr(settings, 'USER', {}))

    try:
        return defaults[key]
    except KeyError:
        raise ImproperlyConfigured('Missing settings: USER[\'{}\']'.format(key))

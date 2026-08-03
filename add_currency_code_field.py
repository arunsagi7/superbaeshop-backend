import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'space_and_beauty.settings')
import django
django.setup()

sys.stdout.reconfigure(encoding='utf-8')

from categories.models import Countries

# ISO 4217 currency codes mapping
currency_codes = {
    'IN': 'INR',  # India
    'US': 'USD',  # United States
    'GB': 'GBP',  # United Kingdom
    'AU': 'AUD',  # Australia
    'CA': 'CAD',  # Canada
    'JP': 'JPY',  # Japan
    'CN': 'CNY',  # China
    'SG': 'SGD',  # Singapore
    'AR': 'ARS',  # Argentina
    'DE': 'EUR',  # Germany
    'FR': 'EUR',  # France
    'IT': 'EUR',  # Italy
    'ES': 'EUR',  # Spain
    'AE': 'AED',  # UAE
    'TH': 'THB',  # Thailand
    'KR': 'KRW',  # South Korea
    'MX': 'MXN',  # Mexico
    'BR': 'BRL',  # Brazil
    'ZA': 'ZAR',  # South Africa
    'RU': 'RUB',  # Russia
    'CH': 'CHF',  # Switzerland
    'SE': 'SEK',  # Sweden
    'NZ': 'NZD',  # New Zealand
}

print("Adding currency_code field to countries...")

for country in Countries.objects.all():
    if country.code in currency_codes:
        country.currency_code = currency_codes[country.code]
    else:
        # Default to USD for unknown countries
        country.currency_code = 'USD'
    country.save()
    print(f"  Updated {country.title}: currency_code={country.currency_code}")

print("\n=== VERIFICATION ===")
for code in ['IN', 'US', 'GB', 'AU', 'SG', 'AR', 'DE', 'AE', 'TH']:
    try:
        c = Countries.objects.get(code=code)
        print(f"{c.title}: code={c.code}, currency_type={c.currency_type}, currency_code={c.currency_code}")
    except Countries.DoesNotExist:

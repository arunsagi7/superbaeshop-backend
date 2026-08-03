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

print("Updating currency codes for countries...")

for country in Countries.objects.all():
    if country.code in currency_codes:
        country.currency_type = currency_codes[country.code]
        country.save()
        print(f"  Updated {country.title}: {country.code} -> {country.currency_type}")
    else:
        # Default to USD for unknown countries
        country.currency_type = 'USD'
        country.save()
        print(f"  Updated {country.title}: {country.code} -> USD (default)")

print("\n=== VERIFICATION ===")
for country in Countries.objects.filter(code__in=['IN', 'US', 'GB', 'AU', 'SG', 'AR', 'DE', 'AE', 'TH']):
    print(f"{country.title}: code={country.code}, currency_type={country.currency_type}")
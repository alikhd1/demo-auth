import requests
from django.conf import settings

class IdentityUtils:
    BASE_URL = f'https://api.kavenegar.com/v1/{settings.KAVENEGAR_API_KEY}'

    @staticmethod
    def send_verification_code(phone: str, code: str, template: str) -> dict:
        url = f'{IdentityUtils.BASE_URL}/verify/lookup.json'
        params = {
            'receptor': phone,
            'token': code,
            'template': template
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
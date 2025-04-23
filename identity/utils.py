import requests
from django.conf import settings

class IdentityUtils:
    BASE_URL = f'https://api.kavenegar.com/v1/{settings.KAVENEGAR_API_KEY}'

    @staticmethod
    def send_sms(phone: str, code: str) -> dict:
        url = f'{IdentityUtils.BASE_URL}/verify/lookup.json'
        params = {
            'receptor': phone,
            'token': code,
            'template': settings.KAVENEGAR_TEMPLATE
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def send_voice_call(phone: str, code: str) -> dict:
        url = f'{IdentityUtils.BASE_URL}/call/maketts.json'
        params = {
            'receptor': phone,
            'message': f'کد تایید شما {code} می‌باشد'
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()

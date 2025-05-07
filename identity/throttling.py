from rest_framework.throttling import SimpleRateThrottle
from rest_framework.exceptions import APIException
from rest_framework import status
from identity.models import UserProfile


class ConditionalUserThrottle(SimpleRateThrottle):
    scope = 'login_user'

    def get_cache_key(self, request, view):
        phone = request.query_params.get('phone')

        if phone and UserProfile.objects.filter(phone=phone).exists():
            self.scope = 'login_user'
            ident = phone
        else:
            self.scope = 'signup_user'
            ident = phone or self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def throttle_failure(self):
        wait = int(self.wait())
        detail = f"تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً {wait} ثانیه دیگر تلاش کنید."
        exception = APIException(detail=detail, code='throttled')
        exception.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        raise exception

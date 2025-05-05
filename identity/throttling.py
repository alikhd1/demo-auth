from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import APIException
from rest_framework import status


class RequestThrottle(AnonRateThrottle):
    scope = 'anon_req'

    def throttle_failure(self):
        wait = int(self.wait())
        detail = f"تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً {wait} ثانیه دیگر تلاش کنید."

        exception = APIException(detail=detail, code='throttled')
        exception.status_code = status.HTTP_429_TOO_MANY_REQUESTS

        raise exception
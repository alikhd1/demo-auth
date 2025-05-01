import uuid
from django.db import models


class UserProfile(models.Model):
    phone = models.CharField(max_length=11, unique=True)
    national_code = models.CharField(max_length=10, unique=True)
    code = models.CharField(max_length=6)
    second_code = models.CharField(max_length=6, null=True, blank=True)
    method = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('call', 'Call'), ('ussd', 'USSD')])
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"PhoneRequest({self.phone}, {self.national_code})"

    class Meta:
        verbose_name = "Phone Request"
        verbose_name_plural = "Phone Requests"



class CaptchaImage(models.Model):
    image_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    code = models.IntegerField()
    image_file = models.ImageField(upload_to='captcha/')
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

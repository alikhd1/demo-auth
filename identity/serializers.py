from rest_framework import serializers
import re


class LoginSerializer(serializers.Serializer):
    national_code = serializers.CharField(max_length=10, min_length=10, required=True)
    method = serializers.ChoiceField(choices=['sms', 'call', 'ussd'], required=True)

    def validate_national_code(self, value):
        national_code_regex = r'^\d{10}$'
        if not re.match(national_code_regex, value):
            raise serializers.ValidationError("کد ملی وارد شده معتبر نیست.")
        return value

    class Meta:
        swagger_schema_fields = {
            "example": {
                "national_code": "1234567890",
                "method": "sms"
            }
        }


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11, min_length=11, required=True)
    national_code= serializers.CharField(max_length=10, min_length=10, required=True)
    method = serializers.ChoiceField(choices=['sms', 'call', 'ussd'], required=True)

    def validate_phone(self, value):
        phone_regex = r'^09\d{9}$'
        if not re.match(phone_regex, value):
            raise serializers.ValidationError("شماره تلفن وارد شده معتبر نیست.")
        return value

    def validate_national_code(self, value):
        national_code_regex = r'^\d{10}$'
        if not re.match(national_code_regex, value):
            raise serializers.ValidationError("کد ملی وارد شده معتبر نیست.")
        return value

    class Meta:
        swagger_schema_fields = {
            "example": {
                "phone": "09123456789",
                "national_code": "1234567890",
                "method": "sms"
            }
        }


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    image_id = serializers.CharField(max_length=50)


    class Meta:
        swagger_schema_fields = {
            "example": {
                "phone": "09123456789",
                "image_id": "6ec7c7fc-937a-4a49-91c1-1f9a7ffe38f3"
            }
        }
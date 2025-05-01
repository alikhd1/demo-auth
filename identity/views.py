import base64
import math
import os

from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .models import UserProfile, CaptchaImage
import random
from .serializers import RegisterSerializer, VerifyCodeSerializer, LoginSerializer
from .utils import IdentityUtils
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import io
import random
import string
import qrcode
from django.http import HttpResponse


class RegisterView(APIView):
    @swagger_auto_schema(
        operation_description="Login using phone number and method",
        request_body=RegisterSerializer,
        responses={200: "ok", 400: 'Bad request'}
    )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']
        national_code = serializer.validated_data['national_code']
        method = serializer.validated_data['method']

        code = str(random.randint(10, 99))

        user = UserProfile.objects.filter(national_code=national_code).first()
        if user:
            return Response({'error': 'User with this national ID already exists'}, status=status.HTTP_400_BAD_REQUEST)

        pr, created = UserProfile.objects.update_or_create(
            phone=phone,
            defaults={'national_code': national_code, 'code': code, 'method': method}
        )

        if method == 'sms':
            IdentityUtils.send_verification_code(phone, code, settings.KAVENEGAR_SMS_TEMPLATE)
        elif method == 'call':
            IdentityUtils.send_verification_code(phone, code, settings.KAVENEGAR_CALL_TEMPLATE)
        else:
            pass

        return Response({'status': 'ok', 'message': 'Code sent successfully'})




class LoginView(APIView):
    @swagger_auto_schema(
        operation_description="Login using phone number and method",
        request_body=LoginSerializer,
        responses={200: "ok", 400: 'Bad request'}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        national_code = serializer.validated_data['national_code']
        method = serializer.validated_data['method']

        if method not in ['sms', 'call', 'ussd']:
            return Response({'error': 'Invalid method'}, status=status.HTTP_400_BAD_REQUEST)

        if not national_code:
            return Response({'error': 'National code is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(national_code=national_code)
            phone = user.phone
        except UserProfile.DoesNotExist:
            return Response({'error': 'Phone number not found for this national code'}, status=status.HTTP_404_NOT_FOUND)

        code = str(random.randint(10, 99))

        user.code = code
        user.save()

        if method == 'sms':
            IdentityUtils.send_verification_code(phone, code, settings.KAVENEGAR_SMS_TEMPLATE)
        elif method == 'call':
            IdentityUtils.send_verification_code(phone, code, settings.KAVENEGAR_CALL_TEMPLATE)
        else:
            pass

        return Response({'status': 'ok', 'message': 'Code sent successfully', 'phone': phone})


class IdentityImageView(APIView):
    @swagger_auto_schema(
        operation_description="Get user by phone",
        manual_parameters=[
            openapi.Parameter(
                'phone',
                openapi.IN_QUERY,
                description="Phone number",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: openapi.Response('OK'), 400: 'Bad request'}
    )
    def get(self, request):
        phone = request.GET.get('phone')
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pr = UserProfile.objects.get(phone=phone)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Phone number not found'}, status=status.HTTP_404_NOT_FOUND)

        options = [random.randint(10, 99) for _ in range(random.randint(5, 10))]
        if pr.code not in options:
            options[random.randint(0, 4)] = int(pr.code)

        response_data = []

        for val in options:
            circle_size = random.randint(120, 180)

            img_size = circle_size + 40
            img = Image.new('RGB', (img_size, img_size), color=(255, 248, 231))
            draw = ImageDraw.Draw(img)

            is_orange = random.choice([True, False])

            if is_orange:
                circle_color = (228, 93, 44)
                text_color = (255, 255, 255)
            else:
                circle_color = (255, 248, 231)
                text_color = (228, 93, 44)

            left_up = ((img_size - circle_size) // 2, (img_size - circle_size) // 2)
            right_down = (left_up[0] + circle_size, left_up[1] + circle_size)

            draw.ellipse([left_up, right_down], fill=circle_color)

            if not is_orange:
                border_width = 6
                for offset in range(border_width):
                    draw.ellipse(
                        [left_up[0]-offset, left_up[1]-offset, right_down[0]+offset, right_down[1]+offset],
                        outline=(228, 93, 44)
                    )

            try:
                font = ImageFont.truetype("arial.ttf", size=circle_size // 3)
            except:
                font = ImageFont.load_default(60)

            text = str(val)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_x = (img_size - bbox[2]) / 2
            text_y = (img_size - bbox[3]) / 2
            draw.text(
                (text_x, text_y),
                text,
                fill=text_color,
                font=font
            )

            image_id = uuid.uuid4()
            filename = f"captcha/{image_id}.png"
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            path = default_storage.save(filename, ContentFile(buffer.getvalue()))

            CaptchaImage.objects.create(
                image_id=image_id,
                user=pr,
                code=val,
                image_file=path
            )

            image_url = os.path.join(settings.MEDIA_URL, filename)
            image_url = f'http://api.irandemo.online{image_url}'
            response_data.append({
                "image_id": str(image_id),
                "image_url": image_url
            })

        return Response(response_data)


class VerifyCodeView(APIView):
    @swagger_auto_schema(
        operation_description="Verify selected code for a phone number",
        request_body=VerifyCodeSerializer,
        responses={200: openapi.Response('Login successful'), 400: 'Bad request'}
    )
    def post(self, request):
        image_id = request.data.get('image_id')
        phone = request.data.get('phone')
        if not image_id or not phone:
            return Response({'error': 'image_id and phone are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pr = UserProfile.objects.get(phone=phone)
            captcha = CaptchaImage.objects.get(image_id=image_id, user=pr, is_valid=True)
        except (UserProfile.DoesNotExist, CaptchaImage.DoesNotExist):
            return Response({'error': 'Invalid phone or image_id'}, status=status.HTTP_400_BAD_REQUEST)


        if int(captcha.code) == int(pr.code):
            captcha.is_valid = False
            captcha.save()
            return Response({'status': 'success'})
        else:
            return Response({'status': 'fail'})


def generate_custom_qr_code(request):
    # Generate random text
    random_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(random_text)
    qr.make(fit=True)

    # Generate QR image with custom colors
    img = qr.make_image(fill_color="#F2ECCF", back_color="#d45930")

    # Save the image to the media folder
    image_name = f"{random_text}.png"
    image_path = os.path.join(settings.MEDIA_ROOT, image_name)

    # Write image to storage
    img.save(image_path)

    # Generate the URL of the saved image
    image_url = os.path.join(settings.MEDIA_URL, image_name)

    return JsonResponse({"qr_code_url": image_url})

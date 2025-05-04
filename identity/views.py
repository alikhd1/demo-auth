import base64
import math
import os

from django.http import HttpResponse, JsonResponse
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import CircleModuleDrawer
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

        second_code = str(random.randint(10, 99))

        while second_code == code:
            second_code = str(random.randint(10, 99))

        user = UserProfile.objects.filter(national_code=national_code).first()
        if user:
            return Response({'error': 'User with this national ID already exists'}, status=status.HTTP_400_BAD_REQUEST)

        pr, created = UserProfile.objects.update_or_create(
            phone=phone,
            defaults={'national_code': national_code, 'code': code, 'second_code': second_code, 'method': method}
        )

        if method == 'sms':
            IdentityUtils.send_verification_code(phone, code, second_code, settings.KAVENEGAR_SMS_TEMPLATE)
        elif method == 'call':
            IdentityUtils.send_verification_code(phone, code, second_code, settings.KAVENEGAR_CALL_TEMPLATE)
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

        second_code = str(random.randint(10, 99))

        while second_code == code:
            second_code = str(random.randint(10, 99))

        user.code = code
        user.second_code = second_code
        user.save()

        if method == 'sms':
            IdentityUtils.send_verification_code(phone, code, second_code, settings.KAVENEGAR_SMS_TEMPLATE)
        elif method == 'call':
            IdentityUtils.send_verification_code(phone, code, second_code, settings.KAVENEGAR_CALL_TEMPLATE)
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
        phone = request.query_params.get('phone')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pr = UserProfile.objects.get(phone=phone)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Phone number not found'}, status=status.HTTP_404_NOT_FOUND)

        options = [random.randint(10, 99) for _ in range(random.randint(5, 10))]

        length = len(options)
        if int(pr.code) not in options:
            options[random.randint(0, length - 1)] = int(pr.code)
        if int(pr.second_code) not in options:
            options[random.randint(0, length - 1)] = int(pr.second_code)

        response_data = []

        for val in options:
            circle_size = random.randint(120, 180)
            img_size = circle_size + 40

            img = Image.new('RGBA', (img_size, img_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            text_color = (128, 127, 125)

            try:
                font = ImageFont.truetype("arial.ttf", size=circle_size // 2)
            except:
                font = ImageFont.load_default()

            text = str(val)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_x = (img_size - bbox[2]) / 2
            text_y = (img_size - bbox[3]) / 2
            draw.text((text_x, text_y), text, fill=text_color, font=font)

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

            image_url = f'http://api.irandemo.online{os.path.join(settings.MEDIA_URL, filename)}'
            response_data.append({
                "image_id": str(image_id),
                "image_url": image_url
            })

        return Response(response_data)

class VerifyCodeView(APIView):
    @swagger_auto_schema(
        operation_description="Verify two selected codes for a phone number (order matters)",
        request_body=VerifyCodeSerializer,
        responses={200: openapi.Response('Verification successful'), 400: 'Bad request'}
    )
    def post(self, request):
        phone = request.data.get('phone')
        image_ids = request.data.get('image_ids')

        if not phone or not image_ids or not isinstance(image_ids, list) or len(image_ids) != 2:
            return Response({'error': 'phone and exactly two image_ids are required in order'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            pr = UserProfile.objects.get(phone=phone)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            captcha1 = CaptchaImage.objects.get(image_id=image_ids[0], user=pr, is_valid=True)
            captcha2 = CaptchaImage.objects.get(image_id=image_ids[1], user=pr, is_valid=True)
        except CaptchaImage.DoesNotExist:
            return Response({'error': 'Invalid image_id or expired image'}, status=status.HTTP_400_BAD_REQUEST)

        if str(captcha1.code) == str(pr.code) and str(captcha2.code) == str(pr.second_code):
            captcha1.is_valid = False
            captcha2.is_valid = False
            captcha1.save()
            captcha2.save()
            return Response({'status': 'success'})
        else:
            return Response({'status': 'fail', 'message': 'Incorrect codes or wrong order'})


def generate_custom_qr_code(request):
    # Generate random text
    random_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(random_text)
    qr.make(fit=True)

    # Create QR code image (black foreground, white background)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # Convert white background to transparent
    pixels = qr_img.getdata()
    new_pixels = []
    for pixel in pixels:
        if pixel[:3] == (255, 255, 255):
            new_pixels.append((255, 255, 255, 0))  # Transparent
        else:
            new_pixels.append(pixel)
    qr_img.putdata(new_pixels)

    # Save the image
    image_name = f"{random_text}.png"
    image_path = os.path.join(settings.MEDIA_ROOT, image_name)
    qr_img.save(image_path, "PNG")

    # Return the image URL
    image_url = os.path.join(settings.MEDIA_URL, image_name)
    return JsonResponse({"qr_code_url": image_url})
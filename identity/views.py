import base64
import math
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .models import UserProfile, CaptchaImage
import random
from .serializers import RegisterSerializer, VerifyCodeSerializer, LoginSerializer
from .utils import IdentityUtils
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

        code = str(random.randint(100, 999))

        user = UserProfile.objects.filter(national_code=national_code).first()
        if user:
            return Response({'error': 'User with this national ID already exists'}, status=status.HTTP_400_BAD_REQUEST)

        pr, created = UserProfile.objects.update_or_create(
            phone=phone,
            defaults={'national_code': national_code, 'code': code, 'method': method}
        )

        if method == 'sms':
            IdentityUtils.send_sms(phone, code)
        elif method == 'call':
            IdentityUtils.send_voice_call(phone, code)
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

        code = str(random.randint(100, 999))

        user.code = code
        user.save()

        if method == 'sms':
            IdentityUtils.send_sms(phone, code)
        elif method == 'call':
            IdentityUtils.send_voice_call(phone, code)
        else:
            pass

        return Response({'status': 'ok', 'message': 'Code sent successfully'})


# class IdentityImageView(APIView):
#     operation_description = "Login using phone",
#
#     @swagger_auto_schema(
#         operation_description="Get user by phone",
#         manual_parameters=[
#             openapi.Parameter(
#                 'phone',
#                 openapi.IN_QUERY,
#                 description="Phone number",
#                 type=openapi.TYPE_STRING
#             )
#         ],
#         responses={200: openapi.Response('OK'), 400: 'Bad request'}
#     )
#
#
#     def get(self, request):
#         phone = request.GET.get('phone')
#         if not phone:
#             return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             pr = UserProfile.objects.get(phone=phone)
#         except UserProfile.DoesNotExist:
#             return Response({'error': 'Phone number not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         options = [random.randint(100, 999) for _ in range(5)]
#         if pr.code not in options:
#             options[random.randint(0, 4)] = int(pr.code)
#
#         width, height = 700, 400
#         img = Image.new('RGB', (width, height), color=(255, 235, 200))
#         draw = ImageDraw.Draw(img)
#
#         try:
#             font = ImageFont.truetype("arial.ttf", 40)
#         except:
#             font = ImageFont.load_default()
#
#         cx, cy = width // 2, height // 2
#         radius = 120
#
#         angle_gap = 360 / len(options)
#         for i, val in enumerate(options):
#             angle = math.radians(angle_gap * i)
#             x = cx + radius * math.cos(angle)
#             y = cy + radius * math.sin(angle)
#
#             draw.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(255, 140, 0))
#
#             text = str(val)
#             text_bbox = draw.textbbox((0, 0), text, font=font)
#             text_width = text_bbox[2] - text_bbox[0]
#             text_height = text_bbox[3] - text_bbox[1]
#
#             text_x = x - text_width // 2
#             text_y = y - text_height // 2
#
#             draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
#
#         buffer = BytesIO()
#         img.save(buffer, format='PNG')
#         buffer.seek(0)
#
#         return HttpResponse(buffer, content_type='image/png')
import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

class IdentityImageView(APIView):
    operation_description = "Login using phone",


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

        options = [random.randint(100, 999) for _ in range(5)]
        if pr.code not in options:
            options[random.randint(0, 4)] = int(pr.code)

        response_data = []

        for val in options:
            img = Image.new('RGB', (200, 200), color=(255, 235, 200))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            draw.ellipse((40, 40, 160, 160), fill=(255, 140, 0))
            text = str(val)
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(
                ((100 - bbox[2] // 2), (100 - bbox[3] // 2)),
                text,
                fill=(255, 255, 255),
                font=font
            )

            image_id = uuid.uuid4()
            filename = f"captcha/{image_id}.png"
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            path = default_storage.save(filename, ContentFile(buffer.getvalue()))

            # Save to DB
            CaptchaImage.objects.create(
                image_id=image_id,
                user=pr,
                code=val,
                image_file=path
            )

            image_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
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
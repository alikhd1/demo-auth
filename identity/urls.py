from django.urls import path
from .views import RegisterView, LoginView, IdentityImageView, VerifyCodeView

urlpatterns = [
    path('', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('identity-image/', IdentityImageView.as_view(), name='identity_image'),
    path('verify/', VerifyCodeView.as_view(), name='verify_code'),
]

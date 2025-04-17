from django.urls import path
from .views import (
    UserRegisterView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    ForgotPasswordView,
    ConfirmCodeView,
    ChangePasswordView,
    ChangeForgotPasswordView,
    UserProfileUpdateView,
    UserMeView,
    GoogleLogin,
    SupportRequestView,
    FacebookLogin,
    UserApplicationsDetail
)



urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('login/google/', GoogleLogin.as_view(), name='google_login'),
    path('login/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegisterView.as_view(), name='user-registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('confirm-code/', ConfirmCodeView.as_view(), name='confirm-code'),
    path('change-forgot-password/', ChangeForgotPasswordView.as_view(), name='change-forgot-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('me/', UserMeView.as_view(), name='users-me'),
    path("support/", SupportRequestView.as_view(), name="support-request"),
    path('me/applications/<int:order_id>/', UserApplicationsDetail.as_view(), name='Applications-detail'),


]





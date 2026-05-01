from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("portal-register-staff/", views.staff_register_view, name="staff_register"),
    path("portal-login-staff/", views.StaffLoginView.as_view(), name="staff_login"),
]

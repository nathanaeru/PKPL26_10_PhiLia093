from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("create/", views.create_post, name="create_post"),
]

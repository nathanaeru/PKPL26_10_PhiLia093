from django.urls import path
from . import views

app_name = "materi"

urlpatterns = [
    path("upload/", views.upload_materi, name="upload"),
    path("<int:pk>/edit/", views.edit_materi, name="edit"),
    path("<int:pk>/delete/", views.delete_materi, name="delete"),
]

from django.urls import path
from . import views

app_name = "assignment"

urlpatterns = [
    path("upload/", views.upload_tugas, name="upload"),
    path("<int:pk>/edit/", views.edit_tugas, name="edit"),
    path("<int:pk>/delete/", views.delete_tugas, name="delete"),
]

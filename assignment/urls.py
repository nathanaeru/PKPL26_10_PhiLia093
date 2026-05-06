from django.urls import path
from . import views

app_name = "assignment"

urlpatterns = [
    path("", views.daftar_tugas, name="daftar_tugas"),
    path("<int:assignment_id>/", views.daftar_submission, name="daftar_submission"),
    path("nilai/<int:submission_id>/", views.beri_nilai, name="beri_nilai"),
    path("upload/", views.upload_tugas, name="upload"),
    path("<int:pk>/edit/", views.edit_tugas, name="edit"),
    path("<int:pk>/delete/", views.delete_tugas, name="delete"),
]

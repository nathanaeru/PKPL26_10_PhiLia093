from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.landing_page, name="landing"),

    path("create/", views.create_post, name="create"),

    path("reply/<int:post_id>/",
         views.reply_post,
         name="reply"),

    path("edit/<int:post_id>/",
         views.edit_post,
         name="edit"),

    path("delete/<int:post_id>/",
         views.delete_post,
         name="delete"),
]
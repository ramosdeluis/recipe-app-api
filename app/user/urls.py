"""
    * Author: Luís Alberto Ramos
    * Date: 06-06-2023

    ? Description: URLs mappings for the user API.

"""
from django.urls import URLPattern, path

from user import views


app_name = "user"

urlpatterns = [path("create/", views.CreateUserView.as_view(), name="create")]

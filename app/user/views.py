"""
    * Author: Luís Alberto Ramos
    * Date: 06-06-2023

    ? Description: Views for the user API

"""
from rest_framework import generics

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer

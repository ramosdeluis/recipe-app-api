"""
    * Author: Luís Alberto Ramos
    * Date: 12-06-2023

    ? Description: Tests for the ingredients API.

"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


URL_INGREDIENTS = reverse("recipe:ingredient-list")


def create_user(email="user@example.com", password="Testpass123"):
    """Creating and return a simple user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsTests(TestCase):
    """Tests for ingredients with users unauthenticated."""

    def setUp(self):
        self.client = APIClient()

    def test_access_denied(self):
        """Testing if the access is denied without autorization."""

        res = self.client.get(URL_INGREDIENTS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsTests(TestCase):
    """Tests for ingredients with an user."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrive_ingredients(self):
        """Test retrieving a list of ingredients."""

        Ingredient.objects.create(user=self.user, name="TestIngOne")
        Ingredient.objects.create(user=self.user, name="TestIngTwo")
        Ingredient.objects.create(user=self.user, name="TestIngTree")

        res = self.client.get(URL_INGREDIENTS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = (
            Ingredient.objects.filter(user=self.user).all().order_by("-name")
        )
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""

        user_two = create_user(
            email="usertwo@example.com", password="testpass123"
        )

        ingred = Ingredient.objects.create(user=self.user, name="TestIngOne")
        Ingredient.objects.create(user=user_two, name="TestIngTwo")

        res = self.client.get(URL_INGREDIENTS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingred.name)
        self.assertEqual(res.data[0]["id"], ingred.id)

"""
    * Author: Luís Alberto Ramos
    * Date: 12-06-2023

    ? Description: Tests for the ingredients API.

"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


URL_INGREDIENTS = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return an ingredient detaild URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


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

    def test_update_ingredient(self):
        """Test updating an ingredient."""

        ingredient = Ingredient.objects.create(
            user=self.user, name="TestIngName"
        )

        payload = {"name": "NewIngTestName", 'amount': '10'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test delete an ingredient is successful."""

        ingredient = Ingredient.objects.create(
            user=self.user, name="TestIngName"
        )

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertNotIn(ingredient, ingredients)

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipe."""

        ing1 = Ingredient.objects.create(user=self.user, name="IngNameOne")
        ing2 = Ingredient.objects.create(user=self.user, name="IngNameTwo")
        recipe = Recipe.objects.create(
            title="TestTitle",
            time_minutes=5,
            price=Decimal("5.0"),
            user=self.user,
        )
        recipe.ingredients.add(ing1)

        res = self.client.get(URL_INGREDIENTS, {"assigned_only": 1})

        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""

        ing = Ingredient.objects.create(user=self.user, name="IngOne")
        Ingredient.objects.create(user=self.user, name="IngTwo")
        recipe1 = Recipe.objects.create(
            title="TestTitle",
            time_minutes=220,
            price=Decimal("120"),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="TestTitleTwo",
            time_minutes=20,
            price=Decimal("10"),
            user=self.user,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(URL_INGREDIENTS, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
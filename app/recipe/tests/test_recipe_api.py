"""
    * Author: Luís Alberto Ramos
    * Date: 07-06-2023

    ? Description: Tests for recipe APIs.

"""
from datetime import datetime
from decimal import Decimal
import tempfile
import os
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""

    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample recepi description.",
        "link": "http://example.om/recipe.pdf",
        "portions": 2.5,
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**params):
    """Create and return a new user."""

    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(
        self,
    ):
        """Test auth is required to call API."""

        res = self.client.get(RECIPES_URL)

        self.assertEqual(
            res.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com",
            password="testpass123",
        )

        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Test retrivering a list of recipes."""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(
            res.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            res.data,
            serializer.data,
        )

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""

        other_user = create_user(
            email="user_two@example.com",
            password="testpass123",
        )

        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializers = RecipeSerializer(
            recipes,
            many=True,
        )

        self.assertEqual(
            res.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            res.data,
            serializers.data,
        )

    def test_get_recipe_detail(
        self,
    ):
        """Test get recipe details."""

        recipe = create_recipe(user=self.user)

        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(
            res.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            res.data,
            serializer.data,
        )

    def test_create_recipe(
        self,
    ):
        """Test creating a recipe."""

        payload = {
            "title": "Test title",
            "price": Decimal("12.34"),
            "time_minutes": 20,
            "portions": 2.5,
            "difficulty": 5,
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""

        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(user=self.user, link=original_link)

        payload = {"title": "New recipe title"}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""

        recipe = create_recipe(self.user)

        payload = {
            "title": "Test new title",
            "price": Decimal("10.99"),
            "time_minutes": 20,
            "description": "Test creating a new description.",
            "link": "https://www.test_example_site.com/recipe",
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""

        recipe = create_recipe(self.user)

        new_user = create_user(email="new_user@example.com")

        url = detail_url(recipe.id)
        self.client.patch(url, user=new_user.id)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""

        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error."""

        other_user = create_user(email="other_user@example.com")

        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tag."""

        payload = {
            "title": "Test Title",
            "time_minutes": 30,
            "price": Decimal("2.99"),
            "tags": [{"name": "Test1"}, {"name": "Test2"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""

        tag = Tag.objects.create(user=self.user, name="TestTag")

        payload = {
            "title": "Test Title",
            "time_minutes": 20,
            "price": Decimal("33.3"),
            "tags": [{"name": "TestTag"}, {"name": "TestTagTwo"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                user=self.user,
                name=tag["name"],
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_upgate(self):
        """Test creating tag when updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "TestTag"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name="TestTag")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""

        tag_one = Tag.objects.create(user=self.user, name="TestTagOne")

        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_one)

        tag_two = Tag.objects.create(user=self.user, name="TestTagTwo")
        payload = {"tags": [{"name": "TestTagTwo"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        all_tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_two, all_tags)
        self.assertNotIn(tag_one, all_tags)

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""

        tag = Tag.objects.create(user=self.user, name="TestTag")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""

        payload = {
            "title": "TestTitle",
            "time_minutes": 10,
            "price": Decimal("10.99"),
            "ingredients": [{"name": "TestIngOne"}, {"name": "TestIngTwo"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test  creating a new recipe with existing ingredient."""

        ingredient = Ingredient.objects.create(
            user=self.user, name="TestIngOne"
        )
        payload = {
            "title": "TestTitle",
            "time_minutes": 20,
            "price": Decimal("10"),
            "ingredients": [{"name": "TestIngOne"}, {"name": "TestIngTwo"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingre in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingre["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "TestIngredient"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertEqual(
            recipe.ingredients.all()[0].name, payload["ingredients"][0]["name"]
        )

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""

        ingredient_one = Ingredient.objects.create(
            user=self.user, name="TestIngName"
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_one)

        ingredient_two = Ingredient.objects.create(
            user=self.user, name="TestIngNameTwo"
        )

        payload = {"ingredients": [{"name": "TestIngNameTwo"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(ingredient_two, recipe.ingredients.all())
        self.assertNotIn(ingredient_one, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""

        ingredient_one = Ingredient.objects.create(
            user=self.user, name="TestNameOne"
        )
        ingredient_two = Ingredient.objects.create(
            user=self.user, name="TestNameTwo"
        )

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_one)
        recipe.ingredients.add(ingredient_two)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags."""

        r1 = create_recipe(user=self.user, title="RecipeOne")
        r2 = create_recipe(user=self.user, title="RecipeTwo")
        tag1 = Tag.objects.create(user=self.user, name="TagOne")
        tag2 = Tag.objects.create(user=self.user, name="TagTwo")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="RecipeTree")

        params = {"tags": f"{tag1.id},{tag2.id}"}
        res = self.client.get(RECIPES_URL, params)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients."""

        r1 = create_recipe(user=self.user, title="RecipeOne")
        r2 = create_recipe(user=self.user, title="RecipeTwo")
        r3 = create_recipe(user=self.user, title="RecipeTree")
        ing1 = Ingredient.objects.create(user=self.user, name="IngOne")
        ing2 = Ingredient.objects.create(user=self.user, name="IngTwo")
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)

        params = {"ingredients": f"{ing1.id},{ing2.id}"}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "passtest123",
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""

        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_wrong_difficulty(self):
        """Creating a recipe with a no valid difficulty (<0 or >5)"""

        payload_one = {"difficulty": 6}
        payload_two = {"difficulty": -1}

        res_one = self.client.post(RECIPES_URL, payload_one)
        res_two = self.client.post(RECIPES_URL, payload_two)

        self.assertEqual(res_one.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_two.status_code, status.HTTP_400_BAD_REQUEST)

    def test_if_when_create_a_recipe_timestamp_is_correct(self):
        """Testing if the timestamp is correctly created"""

        payload = {
            "title": "Test title",
            "price": Decimal("12.34"),
            "time_minutes": 20,
            "portions": 2.5,
            "difficulty": 5,
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        recipe = RecipeDetailSerializer(recipe)

        self.assertIsNotNone(recipe.data["timestamp"])
        self.assertNotEqual(recipe.data["timestamp"], "")

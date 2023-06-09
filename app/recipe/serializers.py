"""
    * Author: Luís Alberto Ramos
    * Date: 09-06-2023

    ? Description: Serializers for recipe API

"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]

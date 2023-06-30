"""
    * Author: Luís Alberto Ramos
    * Date: 19-06-2023

    ? Description: Tests for the health check API.

"""
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """Tests the health check API."""

    def test_health_check(self):
        """Test health check API."""

        client = APIClient()
        url = reverse("health-check")
        res = client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
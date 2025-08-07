from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser

from .models import Project


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

    def test_create_project(self):
        project = Project.objects.create(
            name="Test Project",
            target_url="https://example.com",
            description="This is a test project",
            owner=self.user,
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.description, "This is a test project")


class ProjectAPITest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        self.project_data = {
            "name": "API Test Project",
            "target_url": "https://example.com",
            "description": "Project created via API",
        }

    def test_create_project(self):
        response = self.client.post("/api/projects/", self.project_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, "API Test Project")

    def test_list_projects(self):
        Project.objects.create(
            name="Project 1", target_url="https://example.com", owner=self.user
        )
        Project.objects.create(
            name="Project 2", target_url="https://example.org", owner=self.user
        )

        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_project_detail(self):
        project = Project.objects.create(
            name="Detail Test",
            target_url="https://example.com",
            description="Test description",
            owner=self.user,
        )

        response = self.client.get(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Test")
        self.assertEqual(response.data["description"], "Test description")

from django.db import models

from authentication.models import CustomUser


class Project(models.Model):
    name = models.CharField(max_length=255)
    target_url = models.URLField()
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

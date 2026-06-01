import secrets

from django.contrib.auth.models import User
from django.db import models


class AuthToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="auth_token")
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for_user(cls, user):
        key = secrets.token_hex(32)
        token, _ = cls.objects.update_or_create(user=user, defaults={"key": key})
        return token

    class Meta:
        db_table = "recommendations_authtoken"


class Post(models.Model):
    CATEGORY_CHOICES = [
        ("review", "등산 후기"),
        ("question", "질문"),
        ("safety", "안전 제보"),
        ("general", "자유게시판"),
    ]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    content = models.TextField()
    mountain = models.CharField(max_length=100, blank=True)
    course_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        db_table = "recommendations_post"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        db_table = "recommendations_comment"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="liked_posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
        db_table = "recommendations_postlike"


class HikingRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hiking_records")
    mountain = models.CharField(max_length=100, blank=True)
    course_name = models.CharField(max_length=200)
    hiked_date = models.DateField()
    duration_min = models.PositiveIntegerField(default=0)
    weather_summary = models.CharField(max_length=100, blank=True)
    safety_label = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-hiked_date", "-created_at"]
        db_table = "recommendations_hikingrecord"


class FavoriteCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    course_id = models.CharField(max_length=100)
    course_name = models.CharField(max_length=200)
    mountain = models.CharField(max_length=100, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.PositiveIntegerField(null=True, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course_id")
        ordering = ["-created_at"]
        db_table = "recommendations_favoritecourse"


class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    relation = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        db_table = "recommendations_emergencycontact"

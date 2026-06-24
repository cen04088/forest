import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

TOKEN_EXPIRY_DAYS = 30


class AuthToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="auth_token")
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create_for_user(cls, user):
        key = secrets.token_hex(32)
        expires_at = timezone.now() + timedelta(days=TOKEN_EXPIRY_DAYS)
        token, _ = cls.objects.update_or_create(
            user=user, defaults={"key": key, "expires_at": expires_at}
        )
        return token

    def is_valid(self):
        if self.expires_at is None:
            return True
        return timezone.now() < self.expires_at

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


class SafeLinkSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share_code = models.CharField(max_length=6, unique=True, blank=True)
    course_name = models.CharField(max_length=200, blank=True)
    mountain = models.CharField(max_length=100, blank=True)
    safety_label = models.CharField(max_length=20, blank=True)
    safety_decision = models.CharField(max_length=30, blank=True)
    risk_factors = models.JSONField(default=list)
    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.IntegerField(default=0)
    course_lat = models.FloatField(null=True, blank=True)
    course_lng = models.FloatField(null=True, blank=True)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    location_ts = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="hiking")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendations_safelinksession"
        ordering = ["-created_at"]


class LocationLog(models.Model):
    session = models.ForeignKey(
        SafeLinkSession, on_delete=models.CASCADE, related_name="location_logs"
    )
    lat = models.FloatField()
    lng = models.FloatField()
    recorded_at = models.IntegerField()  # Unix timestamp

    class Meta:
        db_table = "recommendations_locationlog"
        ordering = ["recorded_at"]


class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    relation = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        db_table = "recommendations_emergencycontact"


class MountainKnowledge(models.Model):
    """산림청 API에서 사전 수집한 산 정보 (RAG 검색용)."""
    mountain_name = models.CharField(max_length=100, db_index=True)
    height_m = models.IntegerField(null=True, blank=True)
    region = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    detail = models.TextField(blank=True)
    selection_reason = models.TextField(blank=True)
    source = models.CharField(max_length=30)  # 'culture_info' | 'mountain_story'
    fetched_at = models.DateTimeField(auto_now=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("mountain_name", "source")
        db_table = "recommendations_mountainknowledge"
        indexes = [models.Index(fields=["mountain_name"])]


class TrailCourse(models.Model):
    """국립공원공단 탐방로 CSV → DB 이식본 (RAG + 추천 검색용)."""
    course_id = models.CharField(max_length=60, unique=True)
    mountain = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.IntegerField(null=True, blank=True)
    elevation_gain_m = models.IntegerField(null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    crowding = models.FloatField(default=0.4)
    highlights = models.JSONField(default=list)
    source = models.CharField(max_length=60, blank=True)

    class Meta:
        db_table = "recommendations_trailcourse"
        indexes = [models.Index(fields=["mountain"])]


class DisasterRiskZone(models.Model):
    """국립공원공단 재난위험지구 CSV → DB 이식본 (RAG 검색용)."""
    zone_id = models.CharField(max_length=40, unique=True)
    district = models.CharField(max_length=200, blank=True, db_index=True)
    location = models.CharField(max_length=200, blank=True)
    facility = models.CharField(max_length=200, blank=True)
    risk_factor = models.CharField(max_length=200, blank=True)
    evacuation_place = models.CharField(max_length=200, blank=True)
    search_text = models.TextField(blank=True)

    class Meta:
        db_table = "recommendations_disasterriskzone"
        indexes = [models.Index(fields=["district"])]


class MountainIntro(models.Model):
    """AI가 변환한 산 소개문 (산림청 원문 → 친근한 말투). 1회 생성 후 재사용."""
    mountain_name = models.CharField(max_length=100, unique=True, db_index=True)
    intro = models.TextField()
    raw_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations_mountainintro"


class MountainTags(models.Model):
    """산 매력 태그 (조망·계곡·단풍 등 15종)."""
    mountain_name = models.CharField(max_length=100, unique=True, db_index=True)
    tags = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations_mountaintags"

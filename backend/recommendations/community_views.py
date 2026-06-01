import json
from datetime import date

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import AuthToken, Comment, EmergencyContact, FavoriteCourse, HikingRecord, Post, PostLike


# ── 인증 헬퍼 ─────────────────────────────────────────────────────────────────

def get_auth_user(request):
    key = request.headers.get("X-Auth-Token", "").strip()
    if not key:
        return None
    try:
        return AuthToken.objects.select_related("user").get(key=key).user
    except AuthToken.DoesNotExist:
        return None


def _user_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.first_name or user.username,
        "email": user.email,
        "date_joined": user.date_joined.isoformat(),
    }


def _post_dict(post, user=None):
    is_liked = bool(user and PostLike.objects.filter(post=post, user=user).exists())
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "category_label": dict(Post.CATEGORY_CHOICES).get(post.category, post.category),
        "author": post.author.first_name or post.author.username,
        "author_id": post.author_id,
        "mountain": post.mountain,
        "course_name": post.course_name,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "view_count": post.view_count,
        "like_count": post.likes.count(),
        "comment_count": post.comments.count(),
        "is_liked": is_liked,
        "is_owner": user is not None and user.id == post.author_id,
    }


def _comment_dict(comment, user=None):
    return {
        "id": comment.id,
        "content": comment.content,
        "author": comment.author.first_name or comment.author.username,
        "author_id": comment.author_id,
        "created_at": comment.created_at.isoformat(),
        "is_owner": user is not None and user.id == comment.author_id,
    }


def _parse_body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError):
        return None, JsonResponse({"error": "잘못된 요청입니다."}, status=400)


# ── 인증 API ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def auth_register(request):
    body, err = _parse_body(request)
    if err:
        return err

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    nickname = (body.get("nickname") or "").strip()
    email = (body.get("email") or "").strip()

    if not username or not password:
        return JsonResponse({"error": "아이디와 비밀번호는 필수입니다."}, status=400)
    if len(password) < 6:
        return JsonResponse({"error": "비밀번호는 6자 이상이어야 합니다."}, status=400)
    if len(username) < 3:
        return JsonResponse({"error": "아이디는 3자 이상이어야 합니다."}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "이미 사용 중인 아이디입니다."}, status=400)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=nickname or username,
    )
    token = AuthToken.create_for_user(user)
    return JsonResponse({"token": token.key, "user": _user_dict(user)}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def auth_login(request):
    body, err = _parse_body(request)
    if err:
        return err

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=401)

    if not user.check_password(password):
        return JsonResponse({"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=401)

    token = AuthToken.create_for_user(user)
    return JsonResponse({"token": token.key, "user": _user_dict(user)})


@csrf_exempt
@require_http_methods(["POST"])
def auth_logout(request):
    user = get_auth_user(request)
    if user:
        AuthToken.objects.filter(user=user).delete()
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def auth_me(request):
    user = get_auth_user(request)
    return JsonResponse({"user": _user_dict(user) if user else None})


# ── 게시글 API ────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_list(request):
    user = get_auth_user(request)

    if request.method == "GET":
        qs = Post.objects.select_related("author").prefetch_related("likes", "comments")
        category = request.GET.get("category", "")
        mountain = request.GET.get("mountain", "")
        search = request.GET.get("search", "")
        if category:
            qs = qs.filter(category=category)
        if mountain:
            qs = qs.filter(mountain__icontains=mountain)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

        paginator = Paginator(qs, 15)
        page = paginator.get_page(request.GET.get("page", 1))
        return JsonResponse({
            "posts": [_post_dict(p, user) for p in page.object_list],
            "total": paginator.count,
            "page": page.number,
            "pages": paginator.num_pages,
        })

    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    body, err = _parse_body(request)
    if err:
        return err

    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title or not content:
        return JsonResponse({"error": "제목과 내용은 필수입니다."}, status=400)

    post = Post.objects.create(
        author=user,
        title=title,
        content=content,
        category=body.get("category", "general"),
        mountain=(body.get("mountain") or "").strip(),
        course_name=(body.get("course_name") or "").strip(),
    )
    return JsonResponse(_post_dict(post, user), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def post_detail(request, post_id):
    user = get_auth_user(request)

    try:
        post = Post.objects.select_related("author").prefetch_related(
            "likes", "comments__author"
        ).get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "게시글을 찾을 수 없습니다."}, status=404)

    if request.method == "GET":
        Post.objects.filter(pk=post_id).update(view_count=post.view_count + 1)
        post.refresh_from_db(fields=["view_count"])
        data = _post_dict(post, user)
        data["comments"] = [_comment_dict(c, user) for c in post.comments.all()]
        return JsonResponse(data)

    if not user or user.id != post.author_id:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    if request.method == "DELETE":
        post.delete()
        return JsonResponse({"ok": True})

    body, err = _parse_body(request)
    if err:
        return err

    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title or not content:
        return JsonResponse({"error": "제목과 내용은 필수입니다."}, status=400)

    post.title = title
    post.content = content
    post.category = body.get("category", post.category)
    post.mountain = (body.get("mountain") or post.mountain or "").strip()
    post.course_name = (body.get("course_name") or post.course_name or "").strip()
    post.save()
    return JsonResponse(_post_dict(post, user))


@csrf_exempt
@require_http_methods(["POST"])
def post_like(request, post_id):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "게시글을 찾을 수 없습니다."}, status=404)

    like, created = PostLike.objects.get_or_create(post=post, user=user)
    if not created:
        like.delete()
    return JsonResponse({"is_liked": created, "like_count": post.likes.count()})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_comments(request, post_id):
    user = get_auth_user(request)

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "게시글을 찾을 수 없습니다."}, status=404)

    if request.method == "GET":
        comments = Comment.objects.filter(post=post).select_related("author")
        return JsonResponse({"comments": [_comment_dict(c, user) for c in comments]})

    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    body, err = _parse_body(request)
    if err:
        return err

    content = (body.get("content") or "").strip()
    if not content:
        return JsonResponse({"error": "댓글 내용을 입력해주세요."}, status=400)

    comment = Comment.objects.create(post=post, author=user, content=content)
    return JsonResponse(_comment_dict(comment, user), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def comment_detail(request, comment_id):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "댓글을 찾을 수 없습니다."}, status=404)

    if user.id != comment.author_id:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    comment.delete()
    return JsonResponse({"ok": True})


# ── 내 게시글 ──────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def my_posts(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    qs = Post.objects.filter(author=user).select_related("author").prefetch_related("likes", "comments")
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page", 1))
    return JsonResponse({"posts": [_post_dict(p, user) for p in page.object_list], "total": paginator.count})


@require_http_methods(["GET"])
def liked_posts(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    post_ids = PostLike.objects.filter(user=user).values_list("post_id", flat=True)
    qs = Post.objects.filter(id__in=post_ids).select_related("author").prefetch_related("likes", "comments")
    return JsonResponse({"posts": [_post_dict(p, user) for p in qs]})


# ── 산행 기록 ──────────────────────────────────────────────────────────────────

def _record_dict(r):
    return {
        "id": r.id,
        "mountain": r.mountain,
        "course_name": r.course_name,
        "hiked_date": r.hiked_date.isoformat(),
        "duration_min": r.duration_min,
        "weather_summary": r.weather_summary,
        "safety_label": r.safety_label,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def hiking_records(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    if request.method == "GET":
        records = HikingRecord.objects.filter(user=user)
        return JsonResponse({"records": [_record_dict(r) for r in records]})

    body, err = _parse_body(request)
    if err:
        return err

    hiked_date_str = (body.get("hiked_date") or "").strip()
    try:
        hiked_date = date.fromisoformat(hiked_date_str) if hiked_date_str else date.today()
    except ValueError:
        hiked_date = date.today()

    record = HikingRecord.objects.create(
        user=user,
        mountain=(body.get("mountain") or "").strip(),
        course_name=(body.get("course_name") or "").strip(),
        hiked_date=hiked_date,
        duration_min=int(body.get("duration_min") or 0),
        weather_summary=(body.get("weather_summary") or "").strip(),
        safety_label=(body.get("safety_label") or "").strip(),
    )
    return JsonResponse(_record_dict(record), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def hiking_record_detail(request, record_id):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    HikingRecord.objects.filter(pk=record_id, user=user).delete()
    return JsonResponse({"ok": True})


# ── 즐겨찾기 코스 ─────────────────────────────────────────────────────────────

def _fav_dict(f):
    return {
        "course_id": f.course_id,
        "course_name": f.course_name,
        "mountain": f.mountain,
        "distance_km": f.distance_km,
        "duration_min": f.duration_min,
        "difficulty": f.difficulty,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def favorite_courses(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    if request.method == "GET":
        favs = FavoriteCourse.objects.filter(user=user)
        return JsonResponse({"favorites": [_fav_dict(f) for f in favs]})

    body, err = _parse_body(request)
    if err:
        return err

    course_id = (body.get("course_id") or "").strip()
    if not course_id:
        return JsonResponse({"error": "course_id가 필요합니다."}, status=400)

    fav, created = FavoriteCourse.objects.get_or_create(
        user=user,
        course_id=course_id,
        defaults={
            "course_name": (body.get("course_name") or "").strip(),
            "mountain": (body.get("mountain") or "").strip(),
            "distance_km": body.get("distance_km"),
            "duration_min": body.get("duration_min"),
            "difficulty": (body.get("difficulty") or "").strip(),
        },
    )
    return JsonResponse({"added": created, "course_id": course_id}, status=201 if created else 200)


@csrf_exempt
@require_http_methods(["DELETE"])
def favorite_course_detail(request, course_id):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    FavoriteCourse.objects.filter(user=user, course_id=course_id).delete()
    return JsonResponse({"ok": True})


# ── 긴급 연락처 ──────────────────────────────────────────────────────────────

def _contact_dict(c):
    return {"id": c.id, "name": c.name, "phone": c.phone, "relation": c.relation}


@csrf_exempt
@require_http_methods(["GET", "POST"])
def emergency_contacts(request):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    if request.method == "GET":
        contacts = EmergencyContact.objects.filter(user=user)
        return JsonResponse({"contacts": [_contact_dict(c) for c in contacts]})

    body, err = _parse_body(request)
    if err:
        return err

    name = (body.get("name") or "").strip()
    phone = (body.get("phone") or "").strip()
    if not name or not phone:
        return JsonResponse({"error": "이름과 전화번호는 필수입니다."}, status=400)

    contact = EmergencyContact.objects.create(
        user=user,
        name=name,
        phone=phone,
        relation=(body.get("relation") or "").strip(),
    )
    return JsonResponse(_contact_dict(contact), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def emergency_contact_detail(request, contact_id):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        EmergencyContact.objects.get(pk=contact_id, user=user).delete()
    except EmergencyContact.DoesNotExist:
        return JsonResponse({"error": "찾을 수 없습니다."}, status=404)

    return JsonResponse({"ok": True})

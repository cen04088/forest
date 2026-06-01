from django.contrib.auth.hashers import make_password
from django.db import migrations


SAMPLE_USERS = [
    {"username": "sample_chocoldad",  "nickname": "초코아빠"},
    {"username": "sample_mountainlvr","nickname": "산좋아"},
    {"username": "sample_rainyday",   "nickname": "비오는날"},
]

SAMPLE_POSTS = [
    {
        "author": "sample_chocoldad",
        "title": "초등학생과 90분 코스로 다녀왔어요",
        "content": (
            "초입 화장실 이후에는 쉼터 간격이 길어 물을 미리 챙기는 편이 좋았습니다.\n\n"
            "아이와 함께하는 산행은 페이스 조절이 핵심이에요. 아이가 힘들다고 하면 바로 "
            "쉬어주고, 미리 간식을 챙겨가면 중간 에너지 보충이 됩니다. "
            "초등 저학년 기준으로 90분 이내 코스가 딱 맞았고, 그 이상은 후반에 많이 힘들어했어요."
        ),
        "category": "review",
        "mountain": "",
        "view_count": 47,
    },
    {
        "author": "sample_mountainlvr",
        "title": "부모님과 갈 때 계단 구간은 우회가 좋아요",
        "content": (
            "초반 경사는 완만하지만 중간 데크 계단이 길어 쉬는 시간을 넉넉히 잡았습니다.\n\n"
            "노약자 동반 산행에서 가장 어려운 구간은 계단이에요. 우회로가 있다면 꼭 활용하세요. "
            "시간이 좀 더 걸리더라도 안전하게 다녀오는 것이 훨씬 중요합니다. "
            "무릎이 안 좋으신 부모님과 함께라면 하산 때 스틱을 꼭 챙기는 것도 추천드려요."
        ),
        "category": "review",
        "mountain": "",
        "view_count": 83,
    },
    {
        "author": "sample_rainyday",
        "title": "비 온 다음날은 흙길보다 포장 접근로 추천",
        "content": (
            "미끄러운 구간이 있어 유모차나 보행 보조가 필요한 동반자는 대체 코스가 안전했습니다.\n\n"
            "비 온 직후 흙길은 생각보다 훨씬 미끄럽습니다. 특히 낙엽이 쌓인 구간은 더 위험해요. "
            "보행 보조기구를 사용하시는 분들은 포장된 접근로를 우선 선택하세요. "
            "입산 전날 강수량을 꼭 확인하고 미끄럼 방지 등산화를 착용하는 것도 중요합니다."
        ),
        "category": "safety",
        "mountain": "",
        "view_count": 124,
    },
]

SAMPLE_COMMENTS = [
    {"post_title": "초등학생과 90분 코스로 다녀왔어요",
     "author": "sample_mountainlvr",
     "content": "저도 비슷한 경험이 있어요. 쉼터마다 충분히 쉬어주는 게 핵심인 것 같습니다!"},
    {"post_title": "부모님과 갈 때 계단 구간은 우회가 좋아요",
     "author": "sample_rainyday",
     "content": "정말 공감해요. 저희 아버지도 계단 구간에서 많이 힘드셨는데 우회로 찾길 잘했습니다."},
    {"post_title": "비 온 다음날은 흙길보다 포장 접근로 추천",
     "author": "sample_chocoldad",
     "content": "꼭 필요한 정보 감사합니다. 이번 주말 산행 전에 날씨 다시 확인해봐야겠어요."},
]


def seed_posts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Post = apps.get_model("recommendations", "Post")
    Comment = apps.get_model("recommendations", "Comment")

    users = {}
    for u in SAMPLE_USERS:
        user, _ = User.objects.get_or_create(
            username=u["username"],
            defaults={"first_name": u["nickname"], "password": make_password(None)},
        )
        users[u["username"]] = user

    posts = {}
    for p in SAMPLE_POSTS:
        post = Post.objects.create(
            author=users[p["author"]],
            title=p["title"],
            content=p["content"],
            category=p["category"],
            mountain=p["mountain"],
            view_count=p["view_count"],
        )
        posts[p["title"]] = post

    for c in SAMPLE_COMMENTS:
        post = posts.get(c["post_title"])
        author = users.get(c["author"])
        if post and author:
            Comment.objects.create(post=post, author=author, content=c["content"])


def unseed_posts(apps, schema_editor):
    User = apps.get_model("auth", "User")
    for u in SAMPLE_USERS:
        User.objects.filter(username=u["username"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("recommendations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_posts, reverse_code=unseed_posts),
    ]

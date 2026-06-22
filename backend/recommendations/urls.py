from django.urls import path

from . import views
from . import community_views as cv


urlpatterns = [
    path("health/", views.health),
    path("courses/", views.courses),
    path("data-sources/", views.data_sources),
    path("mountains/", views.mountains),
    path("recommend-mountains/", views.recommend_mountains_view),
    path("vworld-trails/", views.vworld_trails),
    path("local-road-trails/", views.local_road_trails),
    path("mountain-story/", views.mountain_story),
    path("weather/", views.weather),
    path("sun-times/", views.sun_times),
    path("wildfire/", views.wildfire),
    path("landslide/", views.landslide),
    path("recommendations/", views.recommendations),
    path("osm-trails/", views.osm_trails),
    path("disaster-zones/", views.disaster_zones),
    path("safe-links/", views.safe_link_create),
    path("safe-links/by-code/", views.safe_link_by_code),
    path("safe-links/<str:session_id>/", views.safe_link_detail),
    # 인증
    path("auth/register/", cv.auth_register),
    path("auth/login/", cv.auth_login),
    path("auth/logout/", cv.auth_logout),
    path("auth/me/", cv.auth_me),
    # 커뮤니티
    path("posts/", cv.post_list),
    path("posts/<int:post_id>/", cv.post_detail),
    path("posts/<int:post_id>/like/", cv.post_like),
    path("posts/<int:post_id>/comments/", cv.post_comments),
    path("comments/<int:comment_id>/", cv.comment_detail),
    # 안전 제보
    path("safety-reports/", cv.safety_reports),
    # 내 활동
    path("my-posts/", cv.my_posts),
    path("liked-posts/", cv.liked_posts),
    # 산행 기록
    path("hiking-records/", cv.hiking_records),
    path("hiking-records/<int:record_id>/", cv.hiking_record_detail),
    # 즐겨찾기
    path("favorites/", cv.favorite_courses),
    path("favorites/<str:course_id>/", cv.favorite_course_detail),
    # 긴급 연락처
    path("emergency-contacts/", cv.emergency_contacts),
    path("emergency-contacts/<int:contact_id>/", cv.emergency_contact_detail),
    # 대기질 (에어코리아)
    path("air-quality/", views.air_quality),
    # NIFOS 국립산림과학원
    path("nifos-mountain-weather/", views.nifos_mountain_weather),
    path("nifos-fine-dust/", views.nifos_fine_dust),
    # AI
    path("chat/", views.chat_view),
    path("safety-advice/", views.safety_advice_view),
    path("mountain-intro/", views.mountain_intro_view),
]

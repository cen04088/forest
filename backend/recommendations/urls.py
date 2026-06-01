from django.urls import path

from . import views
from . import community_views as cv


urlpatterns = [
    path("health/", views.health),
    path("data-sources/", views.data_sources),
    path("courses/", views.courses),
    path("forest-spatial/", views.forest_spatial),
    path("vworld-trails/", views.vworld_trails),
    path("mountain-story/", views.mountain_story),
    path("weather/", views.weather),
    path("mountain-weather/", views.mountain_weather),
    path("sun-times/", views.sun_times),
    path("wildfire/", views.wildfire),
    path("landslide/", views.landslide),
    path("recommendations/", views.recommendations),
    path("disaster-zones/", views.disaster_zones),
    path("safe-links/", views.safe_link_create),
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
]

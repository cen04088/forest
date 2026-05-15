from django.urls import path

from . import views


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
]

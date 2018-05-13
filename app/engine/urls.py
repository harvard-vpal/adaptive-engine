from django.urls import include, path
from rest_framework import routers
from . import views

app_name = 'engine'

router = routers.DefaultRouter(trailing_slash=False)
router.register('activity', views.ActivityViewSet)
router.register('collection', views.CollectionViewSet)
router.register('score', views.ScoreViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

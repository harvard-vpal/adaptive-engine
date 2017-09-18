from django.conf.urls import include, url
from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register('activity', views.ActivityViewSet)
router.register('collection', views.CollectionViewSet)
router.register('score', views.ScoreViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^testing/', views.testing), # for testing TODO remove
]

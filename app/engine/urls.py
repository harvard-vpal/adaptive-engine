from django.conf.urls import include, url
from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register('activity', views.ActivityViewSet)
router.register('collection', views.CollectionViewSet)
router.register('taglabel', views.TagLabelViewSet)
router.register('tag', views.TagViewSet)
router.register('score', views.TagViewSet)

urlpatterns = [
    url(r'^api/v1/', include(router.urls, namespace='api')),
]

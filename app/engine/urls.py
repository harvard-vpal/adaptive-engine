from django.urls import include, path
from rest_framework import routers
from . import views
from . import api_v2

app_name = 'engine'

router = routers.DefaultRouter(trailing_slash=False)
router.register('activity', views.ActivityViewSet)
router.register('collection', views.CollectionViewSet)
router.register('score', views.ScoreViewSet)
router.register('mastery', views.MasteryViewSet)
router.register('knowledge_component', views.KnowledgeComponentViewSet)

router_v2 = routers.DefaultRouter(trailing_slash=False)
router_v2.register('activity', api_v2.ActivityViewSet)

urlpatterns = [
    path('engine/api/', include(router.urls)),
    path('api/v2/', include(router_v2.urls)),
]

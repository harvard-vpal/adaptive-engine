from django.urls import include, path
from rest_framework import routers
from . import api_v2

app_name = 'engine'

router_v2 = routers.DefaultRouter(trailing_slash=False)
router_v2.register('activity', api_v2.ActivityViewSet)
router_v2.register('collection', api_v2.CollectionViewSet)
router_v2.register('score', api_v2.ScoreViewSet)
router_v2.register('mastery', api_v2.MasteryViewSet)
router_v2.register('knowledge_component', api_v2.KnowledgeComponentViewSet)
router_v2.register('prerequisite_activity', api_v2.PrerequisiteActivityViewSet)
router_v2.register('prerequisite_knowledge_component', api_v2.PrerequisiteKnowledgeComponentViewSet)


urlpatterns = [
    path('api/v2/', include(router_v2.urls)),
    path('engine/api/', include(router_v2.urls)),  # included for backcompatibility through sep 2018
]

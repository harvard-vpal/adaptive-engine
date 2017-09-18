# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework import status

from django.http import HttpResponse

from .serializers import *
from .models import *
from .adaptive_engine import Engine
from .utils import get_engine_settings_for_learner



####

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    # "recommend activity" endpoint
    @list_route()
    def recommend(self, request):
        collection = request.GET.get('collection',None)
        learner = request.GET.get('learner',None)
        # TODO throw error if arguments not found

        # TODO retrieve right engine instance for A/B testing
        engine_settings = get_engine_settings_for_learner(learner)
        engine = Engine(engine_settings)

        activity = engine.recommend(learner, collection)
        return Response(ActivitySerializer(activity).data)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


# "create transaction" endpoint
class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer


### testing
def testing(request):

    # placeholders
    collection = Collection.objects.first()
    learner = Learner.objects.first()

    # TODO retrieve right engine instance for A/B testing
    engine_settings = get_engine_settings_for_learner(learner)
    engine = Engine(engine_settings)

    activity = engine.recommend(learner, collection)

    # TODO fill these in
    learner = None
    activity = None
    score = None
    engine.bayes_update(learner, activity, score)

    return HttpResponse('{}'.format(recommendation))


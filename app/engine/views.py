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
from adaptive_engine import get_engine_for_learner


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
        engine = get_engine_for_learner(learner)

        activity = engine.recommend(learner, collection)

        if activity:
            recommendation_data = ActivityRecommendationSerializer(activity).data
            recommendation_data['complete'] = False
        else:
            recommendation_data = dict(
                collection=collection,
                id=None,
                complete=True,
            )

        return Response(recommendation_data)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


# "create transaction" endpoint
class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

    def get_or_create_learner(self, serializer):
        """
        Not a view - attempts to create learner if serializer data looks
        reasonable and one doesn't exist already
        """
        if serializer.is_valid():
            return serializer.validated_data['learner'], False
        else:
            # check if learner is only field not validating
            if serializer.errors.keys()==['learner']:
                learner_id = serializer.data['learner']
                # check data type
                if isinstance(learner_id,int):
                    try:
                        return Learner.objects.get_or_create(pk=learner_id)
                    except:
                        pass
            return None, None

    # override create behavior
    def create(self, request):
        serializer = ScoreSerializer(data=request.data)
        # create learner if one doesn't exist
        learner, created = self.get_or_create_learner(serializer)
        engine = get_engine_for_learner(learner)
        # initialize matrix data for learner
        if created:
            engine.initialize_learner(learner)
            # reset serializer
            serializer = ScoreSerializer(data=request.data)
        if serializer.is_valid():
            score = Score(**serializer.validated_data)
            # trigger adaptive engine bayes_update
            engine.bayes_update(score)
            # save score to database
            score.save()
            # return response with created score
            return Response(serializer.data)
        else:
            return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


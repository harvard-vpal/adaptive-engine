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
from adaptive_engine import get_engine


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    # "recommend activity" endpoint
    @list_route()
    def recommend(self, request):
        collection = request.GET.get('collection',None)
        learner = request.GET.get('learner',None)

        # throw error if arguments not found
        if not collection and learner:
            return Response(dict(
                message = "Specify learner and collection arguments"
            ))

        # retrieve relevant engine instance for A/B testing
        engine = get_engine(learner)

        # get recommendation from engine
        activity = engine.recommend(learner, collection)
        
        if activity:
            recommendation_data = ActivityRecommendationSerializer(activity).data
            recommendation_data['complete'] = False
        else:
            # engine indicates learner is done with sequence
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

        # initialize matrix data for learner
        if created:
            # get_engine() also assigns the experimental group
            engine = get_engine(learner)
            engine.initialize_learner(learner)
            # reset serializer
            serializer = ScoreSerializer(data=request.data)
        else:
            engine = get_engine(learner)

        # run bayes update and save score
        if serializer.is_valid():
            score = Score(**serializer.validated_data)
            # trigger adaptive engine bayes_update
            engine.update(score)
            # save score to database
            score.save()
            # return response with created score
            return Response(serializer.data)
        else:
            return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


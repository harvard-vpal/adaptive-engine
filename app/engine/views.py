# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import status
from django.http import HttpResponse
from .serializers import *
from .models import *
from .engines import get_engine, initialize_learner
from django.shortcuts import get_object_or_404


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    # "recommend activity" endpoint
    @list_route()
    def recommend(self, request):
        collection_id = request.GET.get('collection',None)
        learner_id = request.GET.get('learner',None)

        # throw error if arguments not found
        if not collection_id and learner_id:
            return Response(dict(
                message = "Specify learner and collection arguments"
            ))

        # get collection object
        collection = get_object_or_404(Collection, pk=collection_id)

        # get or create learner
        learner, created = Learner.objects.get_or_create(pk=learner_id)

        if created:
            # if new learner, assign experimental group, initialize learner params
            initialize_learner(learner)

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
                url=None,
                complete=True,
            )

        return Response(recommendation_data)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    @detail_route(methods=['get','post'])
    def activities(self, request, pk=None):
        collection = self.get_object()
        activities = collection.activity_set.all()
        if request.method == 'POST':
            serializer = CollectionActivitySerializer(activities, data=request.data, many=True, context={'collection':collection})
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = CollectionActivitySerializer(activities, many=True, context={'collection':collection})
        return Response(serializer.data)


def is_valid_except_learner_not_found(serializer):
        """
        Not a view - method to determine whether to go ahead and get/create
        learner based on serializer validity
        """
        if serializer.is_valid():
            return True
        else:
            # check if learner is only field not validating
            if serializer.errors.keys()==['learner']:
                learner_id = serializer.data['learner']
                # check data type
                if isinstance(learner_id,int):
                    return True
            return False

# "create transaction" endpoint
class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

    # override create behavior
    def create(self, request):
        serializer = ScoreSerializer(data=request.data)
        # run validation, catching exception where learner is not found
        if is_valid_except_learner_not_found(serializer):

            # create learner if one doesn't exist
            learner, created = Learner.objects.get_or_create(pk=serializer.data['learner'])

            if created:
                # assign experimental group
                initialize_learner(learner)
                # reset serializer to recognize newly created learner
                serializer = ScoreSerializer(data=request.data)
            
            if serializer.is_valid():
                # get engine
                engine = get_engine(learner)
                # make score object
                score = Score(**serializer.validated_data)
                # trigger update function for engine (bayes update if adaptive)
                engine.update(score)
                # return response with created score
                return Response(serializer.data)
        
        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

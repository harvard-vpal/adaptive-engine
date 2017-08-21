# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response

from .serializers import *
from .models import *


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    # "recommend activity" endpoint
    @detail_route()
    def recommend(self, request, pk=None):
        learner = request.GET.get('learner',None)
        activity = self.get_object().recommend(learner)
        return Response(ActivitySerializer(activity).data)

class TagLabelViewSet(viewsets.ModelViewSet):
    queryset = TagLabel.objects.all()
    serializer_class = TagLabelSerializer

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

# "create transaction" endpoint
class ScoreViewSet(mixins.CreateModelMixin):
    queryset = Tag.objects.all()
    serializer_class = ScoreSerializer

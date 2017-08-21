from rest_framework import serializers
from .models import *

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity 

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection 

class TagLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagLabel

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score

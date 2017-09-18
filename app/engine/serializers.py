from rest_framework import serializers
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity 
        fields = '__all__'


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection 
        fields = '__all__'


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    custom SlugRelatedField that creates the new object when one doesn't exist
    https://stackoverflow.com/a/28011896/
    """

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

class ScoreSerializer(serializers.ModelSerializer):
    learner = CreatableSlugRelatedField(
        queryset = Learner.objects.all(),
        slug_field = 'identifier'
    )

    class Meta:
        model = Score
        fields = ('learner', 'activity', 'score')


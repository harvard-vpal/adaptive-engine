from rest_framework import serializers
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Custom SlugRelatedField that creates the new object when one doesn't exist
    https://stackoverflow.com/a/28011896/
    """

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get_or_create(**{self.slug_field: data})[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')


class CreatablePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Custom PrimaryKeyRelatedField that creates the new object when one doesn't exist
    """

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get_or_create(pk=data)[0]
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection 
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    collection = CreatablePrimaryKeyRelatedField(
        queryset = Collection.objects.all(),
    )
    class Meta:
        model = Activity 
        fields = ('collection','id','name','difficulty','tags')


class ActivityRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('collection','id')


class ScoreSerializer(serializers.ModelSerializer):
    learner = CreatablePrimaryKeyRelatedField(
        queryset = Learner.objects.all(),
    )
    class Meta:
        model = Score
        fields = ('id', 'learner', 'activity', 'score')


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
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            return self.get_queryset().create(pk=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)


class CollectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False)

    class Meta:
        model = Collection 
        fields = '__all__'


class CollectionActivityListSerializer(serializers.ListSerializer):

    def update(self, instance, validated_data):
        """
        Assumes collection instance or id is passed into serializer context at initializtion,
        and is available at self.instance.context
        Adds activities to the collection if they are not already in collection,
        and create new activities or updates fields of existing activities if needed.
        "instance" argument is the queryset of activities currently in the collection
        """
        # Maps for id->instance and id->data item.
        activity_mapping = {activity.url: activity for activity in instance}
        data_mapping = {item['url']: item for item in validated_data}

        # Perform creations, updates and additions to collection
        results = []
        for activity_url, data in data_mapping.items():
            # check if activity with url id exists anywhere
            activity, created = Activity.objects.update_or_create(data, url=activity_url)
            # make sure it is added to collection if within collection context
            activity.collections.add(self.context['collection'])
            results.append(activity)

        # Perform removals from collection.
        for activity_url, activity in activity_mapping.items():
            if activity_url not in data_mapping:
                activity.collections.remove(self.context['collection'])

        return results


class CollectionActivitySerializer(serializers.ModelSerializer):
    """
    Represents activity in the context of a collection
    Separate serializers so that additon/deletion to collection doesn't affect
    membership of activity in other collections
    TODO probably override init to get collection id in
    """
    source_launch_url = serializers.CharField(source='url')
    tags = serializers.CharField(allow_null=True, allow_blank=True, default='')

    def validate_tags(self, value):
        """
        Convert null value into empty string
        """
        if value is None:
            return ''
        else:
            return value

    class Meta:
        model = Activity
        fields = ('source_launch_url', 'name', 'difficulty', 'tags')
        list_serializer_class = CollectionActivityListSerializer


class ActivitySerializer(serializers.ModelSerializer):
    source_launch_url = serializers.CharField(source='url')
    tags = serializers.CharField(allow_null=True, allow_blank=True, default='')

    def validate_tags(self, value):
        """
        Convert null value into empty string
        """
        if value is None:
            return ''
        else:
            return value

    class Meta:
        model = Activity 
        fields = ('collections', 'source_launch_url', 'name', 'difficulty', 'tags')


class ActivityRecommendationSerializer(serializers.ModelSerializer):
    source_launch_url = serializers.CharField(source='url')

    class Meta:
        model = Activity
        fields = ('source_launch_url',)


class ScoreSerializer(serializers.ModelSerializer):
    activity = serializers.SlugRelatedField(
        slug_field='url',
        queryset=Activity.objects.all()
    )

    class Meta:
        model = Score
        fields = ('id', 'learner', 'activity', 'score')


class LearnerFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to use as a compound lookup field in related serializer (e.g. mastery)
    """
    class Meta:
        model = Learner
        fields = ('id', 'user_id', 'tool_consumer_instance_guid')
        # don't enforce unique_together validator on learner user_id/tool_consumer_instance_guid
        # this is so that mastery updates can specify an existing user_id/consumer_id pair
        validators = []


class KnowledgeComponentFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to use in related model serializers (e.g. Mastery)
    """
    class Meta:
        model = KnowledgeComponent
        fields = ('name',)


class MasterySerializer(serializers.ModelSerializer):
    learner = LearnerFieldSerializer()
    knowledge_component = KnowledgeComponentFieldSerializer()

    class Meta:
        model = Mastery
        fields = ('learner', 'knowledge_component', 'value')

    def create(self, validated_data):
        # create referenced learner if it doesn't exist already
        learner_data = validated_data.pop('learner')
        learner, created = Learner.objects.get_or_create(**learner_data)
        # get referenced knowledge component
        knowledge_component_data = validated_data.pop('knowledge_component')
        knowledge_component = KnowledgeComponent.objects.get(**knowledge_component_data)
        # create mastery, but act as an update if mastery object for learner/kc already exists
        mastery, created = Mastery.objects.get_or_create(
            learner=learner,
            knowledge_component=knowledge_component,
            defaults=validated_data
        )
        # update the value field if mastery object for learner/kc already exists
        if not created:
            mastery.value = validated_data['value']
            mastery.save(update_fields=['value'])
        return mastery

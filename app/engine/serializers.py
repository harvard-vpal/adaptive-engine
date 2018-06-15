from rest_framework import serializers
from .models import *


class CollectionSerializer(serializers.ModelSerializer):
    """
    Collection model serializer
    """
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
    Separate serializers so that addition/deletion to collection doesn't affect
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
    """
    Activity model serializer
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
        fields = ('collections', 'source_launch_url', 'name', 'difficulty', 'tags')


class ScoreSerializer(serializers.ModelSerializer):
    """
    Score model serializer
    """
    activity = serializers.SlugRelatedField(
        slug_field='url',
        queryset=Activity.objects.all()
    )

    class Meta:
        model = Score
        fields = ('id', 'learner', 'activity', 'score')


class ActivityRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for recommendation response data
    """
    source_launch_url = serializers.CharField(source='url')

    class Meta:
        model = Activity
        fields = ('source_launch_url',)


class LearnerFieldSerializer(serializers.ModelSerializer):
    """
    Used as a nested serializer for learner foreign key field
    Acts as a "compound lookup field"
    """
    class Meta:
        model = Learner
        # TODO remove id field
        fields = ('id', 'user_id', 'tool_consumer_instance_guid')
        # don't enforce unique_together validator on learner user_id/tool_consumer_instance_guid
        # this is so that mastery updates can specify an existing user_id/consumer_id pair
        validators = []


class KnowledgeComponentFieldSerializer(serializers.ModelSerializer):
    """
    Used as a nested serializer for knowledge_component foreign key field
    """
    # override default serializer field used so that custom field validator can be defined,
    # while ignoring default unique validator
    kc_id = serializers.CharField()

    class Meta:
        model = KnowledgeComponent
        fields = ('kc_id',)

    def validate_kc_id(self, value):
        if KnowledgeComponent.objects.filter(kc_id=value).exists():
            return value
        else:
            raise serializers.ValidationError("Knowledge component with specified kc_id does not exist")


class MasterySerializer(serializers.ModelSerializer):
    """
    Mastery model serializer
    """
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


class KnowledgeComponentSerializer(serializers.ModelSerializer):
    """
    KnowledgeComponent model serializer
    """
    class Meta:
        model = KnowledgeComponent
        fields = ('kc_id', 'name', 'mastery_prior')


class SequenceActivitySerializer(serializers.Serializer):
    """
    Single activity in a activity sequence (provided with recommendation)
    TODO implement this
    """
    pass


class CollectionFieldSerializer(serializers.ModelSerializer):
    """
    Used as a nested serializer for collection foreign key field
    """
    # override default serializer field used so that custom field validator can be defined,
    # while ignoring default unique validator
    collection_id = serializers.CharField()

    class Meta:
        model = Collection
        fields = ('collection_id',)

    def validate_collection_id(self, value):
        """
        Specified collection must exist (create not supported with this serializer)
        :param value:
        :return:
        """
        if Collection.objects.filter(collection_id=value).exists():
            return value
        else:
            raise serializers.ValidationError("object with specified id does not exist")


class ActivityRecommendationRequestSerializer(serializers.Serializer):
    """
    Serializer for incoming activity recommendation request data
    """
    learner = LearnerFieldSerializer()
    collection = CollectionFieldSerializer()
    sequence = serializers.CharField(required=False)  # TODO this could be handled with serializer

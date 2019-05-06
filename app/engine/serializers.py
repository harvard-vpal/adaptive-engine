from rest_framework import serializers, validators
from .models import *


class LearnerSerializer(serializers.ModelSerializer):
    """
    Used as a nested serializer for learner foreign key field
    Acts as a "compound lookup field"
    Supports lookups from creation-like request methods to related objects
    """
    class Meta:
        model = Learner
        fields = ('user_id', 'tool_consumer_instance_guid')

    def run_validators(self, value):
        """
        Modify base run_validators() to not enforce unique_together validator on user_id/tool_consumer_instance_guid
        field combination. This is so that creation-like methods (e.g. put/post) on related objects (e.g. mastery)
        can reference an existing learner (using the user_id/consumer_id pair).
        """
        for validator in self.validators:
            if isinstance(validator, validators.UniqueTogetherValidator):
                self.validators.remove(validator)
        super().run_validators(value)


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
        """
        Custom validation on kc_id field, that verifies that a KnowledgeComponent with the given kc_id exists.
        :param value:
        :return:
        """
        if KnowledgeComponent.objects.filter(kc_id=value).exists():
            return value
        else:
            raise serializers.ValidationError("Knowledge component with specified kc_id does not exist")


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


class CollectionSerializer(serializers.ModelSerializer):
    """
    Collection model serializer
    """
    class Meta:
        model = Collection
        fields = '__all__'
        lookup_field = 'collection_id'  # lookup based on collection_id slug field


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
        fields = ('id', 'collections', 'source_launch_url', 'name', 'difficulty', 'tags', 'knowledge_components',
                  'prerequisite_activities')


class MasterySerializer(serializers.ModelSerializer):
    """
    Mastery model serializer
    """
    learner = LearnerSerializer()
    knowledge_component = KnowledgeComponentFieldSerializer()

    class Meta:
        model = Mastery
        fields = ('learner', 'knowledge_component', 'value')

    def create(self, validated_data):
        """
        Defines write behavior for nested serializers
        Supports auto creation of related learner if they do not exist yet
        Does not support auto creation of new knowledge components if they do not exist yet
        TODO does it make sense to move related object auto creation to view perform_create() instead?
        :param validated_data: validated incoming data (serializer.validated_data)
        :return:
        """
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


class ScoreSerializer(serializers.ModelSerializer):
    """
    Score model serializer
    """
    learner = LearnerSerializer()
    activity = serializers.SlugRelatedField(
        slug_field='url',
        queryset=Activity.objects.all()
    )

    class Meta:
        model = Score
        fields = ('learner', 'activity', 'score')

    def create(self, validated_data):
        """
        Defines write behavior for nested serializer
        Supports auto creation of related learner if doesn't exist yet

        :param validated_data: validated incoming data (serializer.validated_data)
        :return: Score model instance
        """
        # create related learner if it doesn't exist already
        learner_data = validated_data.pop('learner')
        learner, created = Learner.objects.get_or_create(**learner_data)
        # get related activity
        activity = validated_data.pop('activity')
        # create the score object
        score = Score.objects.create(
            learner=learner,
            activity=activity,
            score=validated_data.pop('score')
        )
        return score


class KnowledgeComponentSerializer(serializers.ModelSerializer):
    """
    KnowledgeComponent model serializer
    """
    class Meta:
        model = KnowledgeComponent
        fields = ('id', 'kc_id', 'name', 'mastery_prior')
        lookup_field = 'kc_id'  # lookup based on kc_id slug field


class ActivityRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for recommendation response data
    """
    source_launch_url = serializers.CharField(source='url')

    class Meta:
        model = Activity
        fields = ('source_launch_url',)


class SequenceActivitySerializer(serializers.Serializer):
    """
    Serializer for activity in a sequence list
    (used for parsing sequence list in recommendation request)
    """
    activity = serializers.CharField(source='url')
    score = serializers.FloatField(allow_null=True)
    is_problem = serializers.BooleanField(required=False)

    class Meta:
        model = Activity
        fields = ('activity', 'score', 'is_problem')


class ActivityRecommendationRequestSerializer(serializers.Serializer):
    """
    Serializer for incoming activity recommendation request data
    """
    learner = LearnerSerializer()
    collection = serializers.SlugRelatedField(
            slug_field='collection_id',
            queryset=Collection.objects.all()
        )
    sequence = SequenceActivitySerializer(many=True)


class CollectionActivityListSerializer(serializers.ListSerializer):

    def update(self, instance, validated_data):
        """
        Assumes collection instance or id is passed into serializer context at initialization,
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


class PrerequisiteActivitySerializer(serializers.ModelSerializer):
    """
    Model serializer for Activity.prerequisite_activities.through
    """
    class Meta:
        model = Activity.prerequisite_activities.through
        # from_activity: dependent activity
        # to_activity: prerequisite activity
        fields = ('id','from_activity','to_activity')


class PrerequisiteRelationSerializer(serializers.ModelSerializer):
    """
    Model serializer for PrerequisiteRelation
    """
    class Meta:
        model = PrerequisiteRelation
        fields = ('prerequisite','knowledge_component','value')


class CollectionActivityMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for Collection-Activity membership relation
    """
    class Meta:
        model = Activity.collections.through
        fields = ['id', 'activity', 'collection']

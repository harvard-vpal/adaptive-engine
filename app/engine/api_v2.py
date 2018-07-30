import logging
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .serializers import *
from .models import *
from .engines import get_engine


log = logging.getLogger(__name__)


class ActivityViewSet(viewsets.ModelViewSet):
    """
    Activity-related API endpoints

    Standard CRUD endpoints:
        GET /activity - list
        POST /activity - create
        GET /activity/{id} - retrieve
        PUT /activity/{id} - update
        PATCH /activity/{id} - partial update
        DELETE /activity/{id} - destroy

    Additional endpoints:
        POST /activity/recommend - recommend activity
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    @action(methods=['post'], detail=False)
    def recommend(self, request):
        """
        Recommends an activity
        TODO add "context" argument that includes sequence data

        POST /activity/recommend
        Request Body:
            {
                learner: {
                    'tool_consumer_instance_guid': <str>,
                    'user_id': <str>
                }
                collection: <str>
                sequence: [
                    {
                        activity: <str: url>,
                        score: <float>,
                        is_problem: <bool>,
                    },
                    ...
                ]

            }
        """
        # validate request serializer
        serializer = ActivityRecommendationRequestSerializer(
            data=request.data,
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get learner (creation of learner is supported here if learner does not already exist)
        learner, created = Learner.objects.get_or_create(**serializer.data['learner'])

        # get collection
        collection = serializer.validated_data['collection']

        # parse sequence data
        sequence_data = serializer.validated_data['sequence']
        sequence = []
        for activity_data in sequence_data:
            try:
                sequence.append(Activity.objects.get(url=activity_data['url']))
            except Activity.DoesNotExist:
                log.error("Unknown activity found in sequence data: {}".format(activity_data))

        # get recommendation from engine
        recommended_activity = get_engine().recommend(learner, collection, sequence)

        # construct response data
        if recommended_activity:
            recommendation_data = ActivityRecommendationSerializer(recommended_activity).data
            recommendation_data['complete'] = False
        else:
            # Indicate that learner is done with sequence
            recommendation_data = dict(
                collection=collection,
                url=None,
                complete=True,
            )

        return Response(recommendation_data)


class CollectionViewSet(viewsets.ModelViewSet):
    """
    Collection-related API endpoints

    Standard CRUD endpoints:
        GET /collection - list
        POST /collection - create
        GET /collection/{slug} - retrieve
        PUT /collection/{slug} - update
        PATCH /collection/{slug} - partial update
        DELETE /collection/{slug} - destroy

    Additional endpoints:
        GET /collection/{slug}/activities - list activities in collection
        POST /collection/{slug}/activities - modify activities in collection
        POST /collection/grade - get collection grade for a learner
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    lookup_field = 'collection_id'  # lookup based on collection_id slug field

    @action(methods=['get', 'post'], detail=True)
    def activities(self, request, collection_id=None):
        """
        Handles two API endpoints:

        1. Get activities in collection
            GET /<collection_id>

        2. Update activities in collection
            POST /<collection_id>

            Request body: list of activities that exist in collection
                [
                    {
                        source_launch_url: <https://example.com/1>,
                        name: <str>,
                        tags: <str>,
                        type: <str>,
                        difficulty: <float>
                    },
                    {
                        source_launch_url: <https://example.com/2>,
                        name: <str>,
                        tags: <str>,
                        type: <str>,
                        difficulty: <float>
                    },
                    ...
                ]

            Update behavior:
            - Any activities that do not already exist (based on source_launch_url) will be created,
            and will belong to the relevant collection.
            - Any activities that already exist in the collection will have their fields updated based on the new data.
            - Any activities that existed in the collection previously but are not included in the new request data will
            be removed from the collection (but not deleted from the engine).
        """
        collection, created = Collection.objects.get_or_create(collection_id=collection_id)
        activities = collection.activity_set.all()
        if request.method == 'POST':
            serializer = CollectionActivitySerializer(
                activities,
                data=request.data,
                many=True,
                context={'collection': collection}
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = CollectionActivitySerializer(
                activities,
                many=True,
                context={'collection': collection}
            )
        return Response(serializer.data)

    @action(methods=['post'], detail=True)
    def grade(self, request, collection_id=None):
        """
        Returns a grade between 0.0 and 1.0 for the specified learner and collection.

        POST /collection/{collection_id}/grade
        Request Body:
            {
                learner: {
                    'tool_consumer_instance_guid': str,
                    'user_id': str
                }
            }
        """
        collection = self.get_object()
        # get learner
        serializer = LearnerSerializer(data=request.data['learner'])
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # get or create learner
        learner, created = Learner.objects.get_or_create(**serializer.data)

        grade = collection.grade(learner)
        return Response({'learner': serializer.data, 'grade': grade})


class MasteryViewSet(viewsets.ModelViewSet):
    """
    Mastery-related API endpoints.

    Standard CRUD endpoints:
        GET /mastery - list
        POST /mastery - create
        GET /mastery/{id} - retrieve
        PUT /mastery/{id} - update
        PATCH /mastery/{id} - partial update
        DELETE /mastery/{id} - destroy

    Additional endpoints:
        PUT /mastery/bulk_update - bulk update
    """
    queryset = Mastery.objects.all()
    serializer_class = MasterySerializer

    @action(methods=['put'], detail=False)
    def bulk_update(self, request):
        """
        Receive and create list of mastery objects
        Update mastery value if value has changed
        TODO would like to revert kc dict representation back to string (but keep backcompatibility through sept 2018)
        """
        serializer = MasterySerializer(
            data=request.data,
            many=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KnowledgeComponentViewSet(viewsets.ModelViewSet):
    """
    Collection-related API endpoints

    Standard CRUD endpoints:
        GET /knowledge_component - list
        POST /knowledge_component - create
        GET /knowledge_component/{kc_id} - retrieve
        PUT /knowledge_component/{kc_id} - update
        PATCH /knowledge_component/{kc_id} - partial update
        DELETE /knowledge_component/{kc_id} - destroy
    """
    queryset = KnowledgeComponent.objects.all()
    serializer_class = KnowledgeComponentSerializer
    lookup_field = 'kc_id'  # lookup based on kc_id slug field


class ScoreViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD endpoints:
        GET /grade - list
        GET /grade/{id} - retrieve
        PUT /grade/{id} - update
        PATCH /grade/{id} - partial update
        DELETE /grade/{id} - destroy

    Modified CRUD endpoints:
        POST /grade - create, also supports auto creation of related learners
    """
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

    def perform_create(self, serializer):
        """
        Extend the saving method for the serialized object to include additional
        engine actions afterwards
        :param serializer: serializer representing model object to save
        :return: None
        """
        # required for perform_create()
        score = serializer.save()

        # trigger update function for engine (bayes update if adaptive)
        log.debug("Triggering engine update from score")
        engine = get_engine()
        engine.update_from_score(score.learner, score.activity, score.score)

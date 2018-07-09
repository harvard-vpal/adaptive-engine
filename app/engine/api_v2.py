from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .serializers import *
from .models import *
from .engines import get_engine


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

        POST /activity/recommend
        Request Body:
            {
                learner: {
                    'tool_consumer_instance_guid': str,
                    'user_id': str
                }
                collection: {
                    'collection_id': str
                }
                sequence: [
                    {
                        activity: <source_launch_url>,
                        score: <score>,
                        is_problem: Bool,
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
        collection = Collection.objects.get(**serializer.data['collection'])

        # get sequence
        sequence = serializer.data['sequence']

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

    @action(methods=['get', 'post'], detail=True)
    def activities(self, request, pk=None):
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
        # TODO create collection based on string id
        collection, created = Collection.objects.get_or_create(pk=pk)
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
    def grade(self, request):
        """
        Returns a grade between 0.0 and 1.0 for the specified learner and collection.

        POST /collection/grade
        Request Body:
            {
                learner: {
                    'tool_consumer_instance_guid': str,
                    'user_id': str
                }
                collection: {
                    'collection_id': str
                }
            }
        """
        collection = self.get_object()
        try:
            # TODO this should be a serializer
            learner_id = int(request.data.get('learner', None))
        except:
            msg = "Learner id not provided, or not valid"
            return Response({'message': msg}, status=status.HTTP_400_BAD_REQUEST)
        grade = collection.grade(learner_id)
        return Response({'grade': grade, 'learner': learner_id})

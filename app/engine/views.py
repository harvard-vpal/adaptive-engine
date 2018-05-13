from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from rest_framework import status
from .serializers import *
from .models import *
from .engines import get_engine


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    @list_route(methods=['post'])
    def recommend(self, request):
        """
        API endpoint: Recommend activity
        /engine/api/activity/recommend
        Body:
            learner: int, learner id  #TODO generalize to string ids?
            collection: int
            sequence: (optional) json of activities that exist in sequence
                [
                    {
                        activity: <source_launch_url>,
                        score: <score>,
                        is_problem: Bool,
                    },
                    ...
                ]
        """
        learner_id = request.data.get('learner', None)
        collection_id = request.data.get('collection', None)
        sequence = request.data.get('sequence', None)

        # throw error if arguments not found
        if not learner_id:
            return Response(dict(message="Specify learner argument"), status=status.HTTP_400_BAD_REQUEST)

        # get collection object
        collection = get_object_or_404(Collection, pk=collection_id)

        # get or create learner
        learner, created = Learner.objects.get_or_create(pk=learner_id)

        if created:
            # if new learner, initialize learner params
            engine = get_engine()
            engine.initialize_learner(learner)
            # assign_experimental_group(learner)

        # retrieve relevant engine instance for A/B testing
        engine = get_engine()

        # get recommendation from engine
        activity = engine.recommend(learner, collection, sequence)

        # construct response data
        if activity:
            recommendation_data = ActivityRecommendationSerializer(activity).data
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
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    @detail_route(methods=['get', 'post'])
    def activities(self, request, pk=None):
        """
        API endpoints:
            Get activities in collection
                GET /engine/api/<collection_id>

            Update activities in collection
                POST /engine/api/<collection_id>
                Body: json list of activities that exist in collection
                    [
                        {
                            name: <str>,
                            tags: <str, str, str>,
                            type: <str>,
                            difficulty: <float>,
                            source_launch_url: <https://example.com/1>,
                        },
                        ...
                    ]

        """
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

    @detail_route(methods=['post'])
    def grade(self, request):
        collection = self.get_object()
        try:
            learner_id = int(request.data.get('learner', None))
        except:
            msg = "Learner id not provided, or not valid"
            return Response({'message': msg}, status=status.HTTP_400_BAD_REQUEST)
        grade = collection.grade(learner_id)
        return Response({'grade': grade, 'learner': learner_id})


def _is_valid_except_learner_not_found(serializer):
    """
    Not a view - method to determine whether to go ahead and get/create
    learner based on serializer validity
    """
    if serializer.is_valid():
        return True
    else:
        # check if learner is only field not validating
        if list(serializer.errors.keys()) == ['learner']:
            learner_id = serializer.data['learner']
            # check data type
            if isinstance(learner_id, int):
                return True
        return False


# "create transaction" endpoint
class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

    # override create behavior
    def create(self, request):
        """
        Submit new score
        POST /engine/api/score
        Saves score and triggers engine update
        Body:
            learner: <int>
            activity: <activity url (see serializer)>
            score: <float>
        """
        serializer = ScoreSerializer(data=request.data)
        # run validation, catching exception where learner is not found
        if _is_valid_except_learner_not_found(serializer):

            # create learner if one doesn't exist
            learner, created = Learner.objects.get_or_create(pk=serializer.data['learner'])

            if created:
                # initialize learner params
                engine = get_engine()
                engine.initialize_learner(learner)
                # reset serializer to recognize newly created learner
                serializer = ScoreSerializer(data=request.data)
            
            if serializer.is_valid():
                # get engine
                engine = get_engine()
                # make score object
                score = Score(**serializer.validated_data)
                # trigger update function for engine (bayes update if adaptive)
                engine.update_from_score(score.learner, score.activity, score.score)
                # return response with created score
                return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .serializers import *
from .models import *
from .engines import get_engine


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    @action(methods=['post'], detail=False)
    def recommend(self, request):
        """
        API endpoint: Recommend activity
        /engine/api/activity/recommend
        Body:
            learner: {
                'tool_consumer_instance_guid': str,
                'user_id': str
            }
            collection: {
                'collection_id': str
            }
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

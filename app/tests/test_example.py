from django.test import TestCase
from .simulators import EngineSimulator
from .initializers import RealInitializer, RealInitializerFromSmeFiles
import numpy as np
from engine.models import *
from .api import EngineApiTestClient
from .utils import create_token


class DataLoading(TestCase):
    """
    Verify the number of objects created during data initialization
    """
    def setUp(self):
        RealInitializer()
        # target values
        self.test_num_collections = 7
        self.num_activities = 435
        self.num_kcs = 37

    def test_num_collections(self):
        """
        Check that the number of Collections initialized is 7
        """
        self.assertEqual(Collection.objects.count(),7)

    def test_num_activities(self):
        """
        Check that the number of Activities initialized is 435
        """
        self.assertEqual(Activity.objects.count(),435)

    def test_num_knowledge_components(self):
        """
        Check that the number of KnowledgeComponents initialized
        is 37
        """
        self.assertEqual(KnowledgeComponent.objects.count(),37)

    def test_num_guess(self):
        """
        Check that the number of Guess paraeters initialized is 
        number of activities * number of knowledge componenents
        """
        self.assertEqual(Guess.objects.count(), self.num_activities*self.num_kcs)


class ApiTest(TestCase):
    """
    Test cases using the engine API
    """
    def setUp(self):
        RealInitializerFromSmeFiles().initialize()
        # self.engine = EngineApiTestClient(token=create_token())
        
    def test_test(self):
        self.assertTrue(True)

    def test_recommend_activity(self):
        """
        Check that we can get a recommendation via the engine API
        """
        recommendation = self.engine.recommend(
            learner=1,
            collection=1,
        )
        print recommendation.json()
        self.assertTrue(recommendation)

    def test_submit_score(self):
        """
        Check that we can get submit a score via the engine API
        and that we see the score saved to the database
        """
        print self.engine.submit_score(
            activity=1,
            score=0.5,
            learner=1,
        ).json()
        self.assertEqual(Score.objects.count(), 1)


class AdaptiveLearnerSequence(TestCase):
    """
    Test cases simulating a sequence of problems
    """
    def setUp(self):
        RealInitializerFromSmeFiles(groups=['A'])
        self.engine = EngineSimulator()

    def simulate_learner_sequence(self, learner_id=None, collection_id=None, num_trials=30):
        """
        Simulates learner actions by repeating the process of asking for a recommendation,
        then submitting an answer for the recommended activity (then asking for another
        recommendation, and so on). Directly uses engine methods rather than the API
        """
        for i in range(num_trials):
            recommendation = self.engine.recommend(learner=learner_id, collection=2)
            print recommendation
            if recommendation:
                score = np.random.uniform()
                self.engine.submit_score(
                    learner=learner_id, 
                    activity=recommendation, 
                    score=score,
                )
            else:
                print "Sequence complete"
                break
    
    def test_single_learner(self):
        """
        Simulate single learner doing a sequence of problems
        """
        np.random.seed(1)
        self.simulate_learner_sequence(learner_id=1, collection_id=2)

    def test_multiple_learners(self):
        """
        Repeat process of simulating single learner doing a sequence of problems
        """
        num_learners = 10
        for learner_id in range(1,num_learners+1):
            print "Learner {}".format(learner_id)
            self.simulate_learner_sequence(learner_id=learner_id, collection_id=2)


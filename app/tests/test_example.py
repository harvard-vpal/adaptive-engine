from django.test import TestCase
from .simulators import EngineSimulator, BridgeSimulator
from .initializers import RealInitializer

class MyExampleTest(TestCase):
    def setUp(self):
        RealInitializer(groups=['A'])
        self.engine = EngineSimulator()

    def test_example(self):
        recommendation = self.engine.recommend(
            learner_id=1, 
            collection_id=1,
        )
        self.assertTrue(recommendation)

        self.engine.submit_score(
            learner_id=1,
            activity_id=1,
            score_value=0.5
        )

    def test_2(self):
        BridgeSimulator(num_learners=10).simulate(self.engine,100)
        # assertion?

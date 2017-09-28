from django.test import TestCase
from .simulators import EngineSimulator, BridgeSimulator

class MyExampleTest(TestCase):
    def setUp(self):
        self.engine = EngineSimulator(num_activities=5, num_collections=1, num_kcs=3)

    def test_1(self):
        self.assertTrue(True)

    def test_2(self):
        BridgeSimulator(num_learners=10).simulate(self.engine,100)
        # assertion?

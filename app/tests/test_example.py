from django.test import TestCase
from simulators import EngineSimulator, BridgeSimulator
from utils import reset_database

class MyExampleTest(TestCase):
    def setUp(self):
        self.engine = EngineSimulator(num_activities=5, num_collections=1, num_kcs=3)

    def tearDown(self):
        reset_database('engine')

    def my_test(self):
        self.assertTrue(True)

    def my_other_test(self):
        self.assertTrue(False)

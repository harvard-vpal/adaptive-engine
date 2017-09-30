from django.test.client import Client
import requests
from rest_framework.test import RequestsClient


class EngineApi(object):
    """
    General API interface to engine
    """
    def __init__(self, host="http://localhost:8000", token=None):
        self.base_url = host+'/engine/api'
        self.headers = {'Authorization': 'Token {}'.format(token)} if token else {}
        self.client = self.get_client()
        self.client.headers.update(self.headers)

    def get_client(self):
        return requests.Session()

    def create_activity(self, **kwargs):
        return self.client.post(
            self.base_url+'/activity',
            json=kwargs
        )
    
    def recommend(self, learner=None, collection=None):
        return self.client.get(
            self.base_url+'/activity/recommend',
            params=dict(learner=learner,collection=collection)
        )
    
    def submit_score(self, learner=None, activity=None, score=None):
        return self.client.post(
            self.base_url+'/score', 
            json=dict(learner=learner,activity=activity,score=score)
        )


class EngineApiTestClient(EngineApi):
    """
    Client for use by django internal unit testing
    """
    def __init__(self, host="http://testserver", token=None):
        super(self.__class__, self).__init__(host, token)
    
    def get_client(self):
        """
        Use Django REST Framework's RequestsClient instead of Requests Sessions
        for internal testing
        """
        return RequestsClient()

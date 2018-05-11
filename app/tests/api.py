from rest_framework.test import RequestsClient
from alosi.engine_api import EngineApi


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

"""
Load testing on recommend and submit_score endpoints
"""

from locust import HttpLocust, TaskSet, task
import random

token = 'placeholder'
headers = {'Authorization': 'Token {}'.format(token)} if token else {}

num_learners = 100

class UserBehavior(TaskSet):
    
    @task(1)
    def recommend(self):
        self.client.get('/activity/recommend',params=dict(
            learner=random.randint(1,num_learners),
            collection=random.randint(1,7)
        ),headers=headers)

    @task(1)
    def submit_score(self):
        self.client.post('/score',json=dict(
            learner=random.randint(1,num_learners),
            activity=random.randint(1,435),
            score=1
        ),headers=headers)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 1000
    max_wait = 9000

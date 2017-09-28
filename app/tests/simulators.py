import numpy as np
from engine.models import *
from django.apps import apps
from engine import engines, utils


class EngineSimulator():
    def __init__(self, num_activities=5, num_collections=1, num_kcs=5,
        slip_probability=0.15, guess_probability=0.1, trans_probability=0.1,
        prior_knowledge_probability=0.2):
        """
        Reset database data and initialize with test environment
        """
        self.num_activities = num_activities
        self.num_collections = num_collections
        self.num_kcs = num_kcs

        utils.reset_database('engine')

        self.initialize_engine_settings()
        self.initialize_experimental_groups()
        self.initialize_collections()
        self.initialize_knowledge_components(prior_knowledge_probability)
        self.initialize_prereqs()
        self.initialize_activities()
        self.initialize_param_matrix(Guess,guess_probability)
        self.initialize_param_matrix(Slip,slip_probability)
        self.initialize_param_matrix(Transit,trans_probability)


    # collections
    def initialize_collections(self):
        Collection.objects.all().delete()

        Collection.objects.bulk_create([Collection(
            pk=pk,
            name="Collection {}".format(pk)
    ) for pk in range(1,self.num_collections+1)])


    def initialize_prereqs(self):
        """
        initialize QxK matrices guess/slip/transit
        """
        model = PrerequisiteRelation
        model.objects.all().delete()
        objs_to_create = []
        for k1 in range(1,self.num_kcs+1):
            for k2 in range(1,self.num_kcs+1):
                objs_to_create.append(
                    model(
                        prerequisite_id=k1,
                        knowledge_component_id=k2,
                        value = np.random.uniform()
                    )
                )
        return model.objects.bulk_create(objs_to_create)

    def initialize_knowledge_components(self, prior_knowledge_probability):
        """
        Initialize knowledge components
        """
        return KnowledgeComponent.objects.bulk_create([KnowledgeComponent(
            pk=pk,
            name="KnowledgeComponent {}".format(pk),
            mastery_prior = utils.odds(prior_knowledge_probability)
        ) for pk in range(1,self.num_kcs+1)])


    def initialize_activities(self):

        activities = Activity.objects.bulk_create([Activity(
            pk=pk,
            name="Activity {}".format(pk),
            difficulty = np.random.uniform(),
            collection_id = np.random.randint(1,self.num_activities+1),
            knowledge_components = [np.random.randint(1,self.num_kcs+1)]
        ) for pk in range(1,self.num_activities+1)])


    def initialize_engine_settings(self):
        default_params = dict(
            L_star = 2.2,
            r_star = 0.0,
            W_p = 5.0,
            W_d = 0.5
        )
        EngineSettings.objects.bulk_create([
            EngineSettings(
                pk=1,
                name="Engine A",
                W_r=2.0,
                W_c=1.0,
                **default_params
            ),
            EngineSettings(
                pk=2,
                name="Engine B",
                W_r=1.0,
                W_c=2.0,
                **default_params
            )
        ])


    def initialize_experimental_groups(self):
        ExperimentalGroup.objects.bulk_create([
            ExperimentalGroup(
                pk=1,
                name="Group A",
                engine_settings_id=1,
            ),
            ExperimentalGroup(
                pk=2,
                name="Group B",
                engine_settings_id=2,
            ),
            ExperimentalGroup(
                pk=3,
                name="Group C"
                # no engine specified for Group C
            )
        ])

    def initialize_param_matrix(self, model, value):
        """
        Initialize (Q x K) matrices: Guess, Slip, Transfer
        """
        model.objects.all().delete()
        objs_to_create = []
        for q in range(1,self.num_activities+1):
            for k in range(1,self.num_kcs+1):
                objs_to_create.append(
                    model(
                        activity_id=q,
                        knowledge_component_id=k,
                        value=utils.odds(value)
                    )
                )
        return model.objects.bulk_create(objs_to_create)

    def submit_score(self, learner_id, activity_id, score_value):
        activity = Activity.objects.get(pk=activity_id)
        learner, created = Learner.objects.get_or_create(pk=learner_id)
        
        if created or not learner.experimental_group:
            engine = engines.get_engine(learner)
            engine.initialize_learner(learner)
        else:
            engine = engines.get_engine(learner)
        score = Score(learner=learner, activity_id=activity_id, score=score_value)
        # do bayes update
        engine.update(score)
        score.save()

    def recommend(self, learner_id, collection_id):
        collection = Collection.objects.get(pk=collection_id)
        learner, created = Learner.objects.get_or_create(pk=learner_id)
        if created or not learner.experimental_group:
            engine = engines.get_engine(learner)
            engine.initialize_learner(learner)
        else:
            engine = engines.get_engine(learner)
        # make recommendation
        recommended_activity = engine.recommend(learner, collection)
        return recommended_activity


class EngineApiInterface(object):
    def __init__(self, host="http://localhost:8000", token=None):
        self.base_url = host+'/engine/api'
        self.headers = {'Authorization': 'Token {}'.format(token)} if token else {}
    def create_activity(self, activity_data):
        r = requests.post(self.base_url+'/activity',headers=self.headers)
    def recommend_activity(self, activity_id, collection_id):
        r = requests.get(self.base_url+'/activity',params=dict(activity=activity_id, collection=collection_id),headers=self.headers)
    def submit_score(self, score_data):
        r = requests.post(self.base_url+'/activity', json=activity)


class EngineApiSimulator(EngineSimulator):
    def __init__(self, engine_api, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        self.engine_api = engine_api
        
    def initialize_activities(self):
        for i in range(self.num_activities):
            pk = i+1
            self.engine_api.create_activity(dict(
                pk=pk,
                name="Activity {}".format(pk),
                # how to initialize knowledge component?
                tags="tag1,tag2"
            ))


class BridgeSimulator(object):
    def __init__(self, num_learners):
        self.num_learners = num_learners
        self.learners = [LearnerSimulator() for i in range(num_learners)]


    def simulate(self, engine, num_trials=100):
        for i in range(num_trials):
            learner_id = np.random.randint(0,len(self.learners))+1
            learner = self.learners[learner_id-1]
            recommendation = engine.recommend(learner_id, collection_id=1)
            if recommendation:
                score = learner.attempt_activity(recommendation)
                engine.submit_score(learner_id,recommendation.pk,score)


class LearnerSimulator(object):
    def __init__(self):
        pass
    def attempt_activity(self, activity):
        return np.random.uniform()

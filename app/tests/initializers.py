"""
Utilities for initializing engine application data
"""
from engine.models import *
from .utils import reset_database, inverse_odds
from engine import utils
import numpy as np
import os
import pandas as pd

def create_and_initialize_learner(learner_id, experimental_group_id=None):
    """
    Create new learners, optionally with a specific experimental group
    Useful for testing
    """
    learner = Learner.objects.create(pk=learner_id)
    initialize_learner(learner_id, experimental_group_id)


class BaseInitializer(object):
    """
    Initializes common models: experiemntal groups / engine settings
    """
    def __init__(self, groups=['A','B','C']):
        """
        groups should be something like ['A','B','C'], or ['A'] to use a single group
        A / B are adaptive groups, C is nonadaptive
        """
        self.groups = groups
        reset_database('engine')
        self.initialize_engine_settings()
        self.initialize_experimental_groups()

    def initialize_engine_settings(self):
        default_params = dict(
            L_star = 2.2,
            r_star = 0.0,
            W_p = 5.0,
            W_d = 0.5
        )
        engine_settings = dict(
            A = EngineSettings(
                pk=1,
                name="Engine A",
                W_r=2.0,
                W_c=1.0,
                **default_params
            ),
            B = EngineSettings(
                pk=2,
                name="Engine B",
                W_r=1.0,
                W_c=2.0,
                **default_params
            ),
            C = None
        )
        EngineSettings.objects.bulk_create([engine_settings[g] for g in self.groups if engine_settings[g]])

    def initialize_experimental_groups(self):
        experimental_groups = dict(
            A = ExperimentalGroup(
                pk=1,
                name="Group A",
                engine_settings_id=1,
            ),
            B = ExperimentalGroup(
                pk=2,
                name="Group B",
                engine_settings_id=2,
            ),
            C = ExperimentalGroup(
                pk=3,
                name="Group C"
                # no engine specified for Group C
            )
        )
        ExperimentalGroup.objects.bulk_create([experimental_groups[g] for g in self.groups])

    
class FakeInitializer(BaseInitializer):
    """
    Engine simulator initialized with some fake data
    Able to control parameters like number of activities, collections, kcs
    """
    def __init__(self, groups=['A','B','C'], num_activities=5, num_collections=1, num_kcs=5,
        slip_probability=0.15, guess_probability=0.1, trans_probability=0.1,
        prior_knowledge_probability=0.2):
        """
        Reset database data and initialize with test environment
        Arguments:
            groups (list): list of group codes, e.g. ['A','B']
            num_activities (int): number of activities to initialize
            num_collections (int): number of activities to initialize
            num_kcs (int): number of knowledge components to initialize
            slip_probability (float): initial value for slip matrix element
            guess_probability (float): initial value for guess matrix element
            trans_probability (float): initial value for trans matrix element
            prior_knowledge_probability (float): initial value for mastery matrix element
        """
        # initialize experimental groups and engine settings
        super(self.__class__, self).__init__(groups=groups)

        self.num_activities = num_activities
        self.num_collections = num_collections
        self.num_kcs = num_kcs

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

class RealInitializer(BaseInitializer):
    """
    Initialize with realistic data for adaptive study
    Only A and B groups
    """
    
    def __init__(self, repo_path=None, groups=['A','B']):
        """
        Arguments:
            repo_path: path to the github repo, e.g. /Users/me/github/adaptive-engine
            groups: list of group codes
        """
        # initialize experimental groups and engine settings
        super(self.__class__, self).__init__(groups=groups)

        
        # this is path to the github repository on your machine
        if repo_path:
            self.repo_path = repo_path
        else:
            self.repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.initialization_prep()
        self.initialize_collections()
        self.initialize_knowledge_components()
        self.initialize_prereqs()
        self.initialize_activities()
        self.initialize_param_matrices()

        
    def load_tagging_data(self):

        def load_data(name):
            tagging_data_dir = os.path.join(self.repo_path, 'data/tagging_data')
            return pd.read_csv("{}/{}.csv".format(tagging_data_dir,name),header=None)

        data = {}
        tables = ['difficulty','items','KCs','L_i','m_guess','m_slip','m_tagging','m_trans','m_w','modules','scope']
        vectors = ['difficulty','items','KCs','modules']
        for table in tables:
            data[table] = load_data(table)
            if table in vectors:
                data[table] = data[table][0]
            elif table == 'L_i':
                data[table] = data[table].T
        return data

    def make_collection_df(self):
        """
        Make dataframe with collection data
        """
        df_collections = pd.DataFrame({'collection_id':range(1,8),'name':[
            'Module 1','Module 2','Module 3','Module 4','Module 5',
            'Pretest','Final'
        ]})

        df_collections = pd.DataFrame([
            dict(name='Pre-test', collection_id=1, max_problems=64),
            dict(name='Module 1', collection_id=2, max_problems=15),
            dict(name='Module 2', collection_id=3, max_problems=22),
            dict(name='Module 3', collection_id=4, max_problems=28),
            dict(name='Module 4', collection_id=5, max_problems=18),
            dict(name='Module 5', collection_id=6, max_problems=50),
            dict(name='Post-test', collection_id=7, max_problems=108),
        ])
        return df_collections

    def make_adaptive_item_df(self):
        df_adaptive_items = (pd.DataFrame([dict(
                item_id =item_id,
                name = "Adapt {}".format(item_id),
                collection_id = self.activity_collections[idx]+1,
                include_adaptive=True,
                # difficulty defined as odds in this file - convert back to between 0 and 1
                difficulty = np.round(inverse_odds(self.data['difficulty'][idx]),2),
            ) for idx, item_id in self.data['items'].iteritems()
            ])
        )

        # adding preadaptive order here for certain modules
        df_adaptive_items['preadaptive_order'] = (df_adaptive_items
             .assign(order=None)
            # fixed portion of pre/post-tests for adaptive groups
            # id=6 is preadaptive post-test portion
            # id=8 is preadaptive pre-test portion
             .query('collection_id==[6,8]')
             .groupby('collection_id')
             .order
             .transform(lambda x: range(1,len(x)+1))
        )
        # merge the collection ids for (6,7) and (8,9)
        # reassign so that order is pretest, 5 modules, post-test
        collection_id_mapping = {
            1:2, # id 2 is module 1
            2:3, # id 3 is module 2
            3:4, 
            4:5,
            5:6,
            6:7, # id 7 is post test
            7:7,
            8:1, # id 1 is pre test
            9:1,
        }
        df_adaptive_items['collection_id'] = df_adaptive_items.collection_id.apply(lambda x: collection_id_mapping[x])
        return df_adaptive_items


    def make_activity_df(self):
        """
        Can combine non-adpative and adaptive here in subclass
        """
        return self.df_adaptive_items.assign(pk=lambda x: x.index+1)


    def initialization_prep(self):
        """
        Prepare dataframes / arrays to use for database object population
        """
        # load matrices from files
        self.data = self.load_tagging_data()

        # activity_collections[activity_pk-1] will return collection_id (pre-remapping) for that activity
        self.activity_collections = self.data['scope'].stack().groupby(level=0).apply(lambda x: x[x==1].index[0][1])

        # activity_tagging[activity_pk-1] will return kc_id-1 for that activity
        self.activity_tagging = self.data['m_tagging'].stack().groupby(level=0).apply(lambda x: x[x==1].index[0][1])

        # prepare dataframes
        self.df_collections = self.make_collection_df()

        self.df_adaptive_items = self.make_adaptive_item_df()
        self.df_activities = self.make_activity_df()


    def initialize_collections(self):
        """
        Create collection objects in database
        """
        # create collections
        Collection.objects.bulk_create([
            Collection(
                pk = row.collection_id,
                name = row.name,
            ) for row in self.df_collections.itertuples()
        ])

    def initialize_knowledge_components(self):
        """
        Create KC objects in database
        """
        # create KC
        KnowledgeComponent.objects.bulk_create([
            KnowledgeComponent(
                pk = idx+1,
                name = name,
                mastery_prior = self.data['L_i'].loc[idx]
            ) for idx, name in self.data['KCs'].iteritems()
        ])

    def replace_nan_none(self, x):
        """
        Returns the same value, but replaces NaN with None
        Used when setting an integer model field with np/pd NaN
        """
        return x if pd.notnull(x) else None
        
    def initialize_activities(self):
        """
        Create activity objects in database
        """

        # create activities from df

        # create activities
        activities = Activity.objects.bulk_create([
            Activity(
                pk = row.pk,
                collection_id = row.collection_id,
                name = row.name,
                difficulty = row.difficulty,
                include_adaptive = self.replace_nan_none(row.include_adaptive),
                preadaptive_order = self.replace_nan_none(row.preadaptive_order),
            ) for row in self.df_activities.itertuples()
        ])
        # add in knowledge component tagging
        for idx in self.activity_tagging:
            activities[idx].knowledge_components.add(self.activity_tagging[idx]+1)

    def initialize_prereqs(self):
        """
        Create prereq objects in database
        """
        # populate pre req
        prereqs = []
        for x, row in enumerate(self.data['m_w'].as_matrix()):
            for y, value in enumerate(row):
                prereqs.append(PrerequisiteRelation(
                    prerequisite_id = x+1,
                    knowledge_component_id = y+1,
                    value = value
                ))
        PrerequisiteRelation.objects.bulk_create(prereqs)

    def initialize_param_matrices(self):
        """
        Create guess/slip/transit parameters in database
        """

        model_data = {
            Guess: self.data['m_guess'],
            Slip: self.data['m_slip'],
            Transit: self.data['m_trans'],
        }

        for model in model_data:
            objs = []
            for x, row in enumerate(model_data[model].as_matrix()):
                for y, value in enumerate(row):
                    objs.append(model(
                        activity_id = x+1,
                        knowledge_component_id = y+1,
                        value = value
                    ))
            model.objects.bulk_create(objs)



class RealAdaptiveNonadaptiveInitializer(RealInitializer):
    """
    Initialize with realistic data for adaptive study
    """
    
    def __init__(self, repo_path=None, groups=['A','B','C']):
        """
        Arguments:
            repo_path: path to the github repo, e.g. /Users/me/github/adaptive-engine
            groups: list of group codes
        """
        # initialize experimental groups and engine settings
        super(self.__class__, self).__init__(repo_path=repo_path, groups=groups)


    def make_nonadaptive_item_df(self):
        """
        Make df of nonadaptive item info
        Loads and uses separate spreadsheet from tagging data
        Requires self.df_collections to be set
        """
        df_nonadaptive_items = pd.read_csv(os.path.join(self.repo_path,'data/items_KC_Group_C_marked.csv'))

        order = (df_nonadaptive_items
            .assign(order=None)
            .sort_values('Item.ID')
            .groupby('Module')
            .order
            .transform(lambda x: range(1,len(x)+1))
        )

        df_nonadaptive_items = (df_nonadaptive_items
            .assign(nonadaptive_order=order)
            .merge(self.df_collections,left_on='Module',right_on='name')
            .rename(columns={
                  'Item.ID':'item_id',
                  'Item.name':'name'
            })
            [['item_id','collection_id','nonadaptive_order']]
        )
        return df_nonadaptive_items


    def make_activity_df(self):
        """
        create activity table by combining adaptive item table and non-adaptive item table
        Requires self.df_adaptive_items and self.df_nonadaptive_items to be set
        """
        df_activities = (self.df_adaptive_items
            # join on both (collection_id, item_id)
            .merge(self.df_nonadaptive_items,how='outer')
            .assign(pk=lambda x: x.index+1)
        )
        df_activities['include_adaptive'].fillna(False,inplace=True)
        return df_activities


    def initialization_prep(self):
        """
        Prepare dataframes / arrays to use for database object population
        """
        # load matrices from files
        self.data = self.load_tagging_data()

        # activity_collections[activity_pk] will return collection_id for that activity
        self.activity_collections = self.data['scope'].stack().groupby(level=0).apply(lambda x: x[x==1].index[0][1])

        # activity_tagging[activity_pk] will return kc_id-1 for that activity
        self.activity_tagging = self.data['m_tagging'].stack().groupby(level=0).apply(lambda x: x[x==1].index[0][1])

        # prepare dataframes
        self.df_collections = self.make_collection_df()
        self.df_nonadaptive_items = self.make_nonadaptive_item_df()
        self.df_adaptive_items = self.make_adaptive_item_df()
        self.df_activities = self.make_activity_df()


        
    def initialize_activities(self):
        """
        Create activity objects in database
        """

        # create activities from df

        # create activities
        activities = Activity.objects.bulk_create([
            Activity(
                pk = row.pk,
                collection_id = row.collection_id,
                name = row.name,
                difficulty = row.difficulty,
                include_adaptive = self.replace_nan_none(row.include_adaptive),
                nonadaptive_order = self.replace_nan_none(row.nonadaptive_order),
                preadaptive_order = self.replace_nan_none(row.preadaptive_order),
            ) for row in self.df_activities.itertuples()
        ])
        # add in knowledge component tagging
        for idx in self.activity_tagging:
            activities[idx].knowledge_components.add(self.activity_tagging[idx])





# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


def first_and_last_n_chars(s, n1=30, n2=30):
    """
    Utility function to display first n1 characters and last n2 characters of a long string
    (Adjusts display if string is less than n1+n2 char long)
    :param s: string
    :return: string for display
    """
    first_len = min(len(s), n1)
    first = s[:first_len]
    last_len = min(len(s) - len(first), n2)
    last = s[-last_len:] if last_len > 0 else ''

    if first_len == len(s):
        return first
    elif first_len + last_len == len(s):
        return "{}{}".format(first, last)
    else:
        return "{}...{}".format(first, last)


class Collection(models.Model):
    """
    Collection consists of multiple activities
    """
    collection_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    max_problems = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return "Collection: {} ({})".format(self.collection_id, self.name)

    def grade(self, learner):
        """
        Generate learner grade based on masteries that bridge can query
        as a grading policy option.
        TODO Just uses a placeholder value for now - update this
        """
        return 0.5


class KnowledgeComponent(models.Model):
    kc_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    mastery_prior = models.FloatField(null=True, blank=True)

    def __str__(self):
        return "KC: {} ({})".format(self.kc_id, self.name)


class PrerequisiteRelation(models.Model):
    prerequisite = models.ForeignKey(
        KnowledgeComponent,
        on_delete=models.CASCADE,
        related_name="dependent_relation"
    )
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "PrerequisiteRelation: {} (prereq) -> {} = {}".format(
            self.prerequisite.kc_id,
            self.knowledge_component.kc_id,
            self.value
        )


class Activity(models.Model):
    """
    Activity model
    """
    url = models.CharField(max_length=500, default='')
    name = models.CharField(max_length=200, default='')
    collections = models.ManyToManyField(Collection, blank=True)
    knowledge_components = models.ManyToManyField(KnowledgeComponent, blank=True)
    difficulty = models.FloatField(null=True,blank=True)
    tags = models.TextField(default='', blank=True)
    type = models.CharField(max_length=200, default='', blank=True)
    # whether to include as valid problem to recommend from adaptive engine
    include_adaptive = models.BooleanField(default=True)
    # order for non-adaptive problems
    nonadaptive_order = models.PositiveIntegerField(null=True, blank=True)
    # order for pre-adaptive problems
    preadaptive_order = models.PositiveIntegerField(null=True, blank=True)
    # prerequisite activities - used to designate activities that should be served before
    prerequisite_activities = models.ManyToManyField('self', blank=True, symmetrical=False)

    def __str__(self):
        return "Activity: {} ({})".format(first_and_last_n_chars(self.url, 40, 10), self.name)


class EngineSettings(models.Model):
    name = models.CharField(max_length=200, default='')
    r_star = models.FloatField()  # Threshold for forgiving lower odds of mastering pre-requisite LOs.
    L_star = models.FloatField()  # Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered
    W_p = models.FloatField()  # Importance of readiness in recommending the next item
    W_r = models.FloatField()  # Importance of demand in recommending the next item
    W_c = models.FloatField()  # Importance of continuity in recommending the next item
    W_d = models.FloatField()  # Importance of appropriate difficulty in recommending the next item

    def __str__(self):
        return "EngineSettings: {}".format(self.name if self.name else self.pk)


class ExperimentalGroup(models.Model):
    name = models.CharField(max_length=200,default='')
    weight = models.FloatField(default=0)
    engine_settings = models.ForeignKey(
        EngineSettings,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __str__(self):
        return "Experimental Group {}".format(self.name if self.name else self.pk)


class Learner(models.Model):
    """
    User model for students
    """
    user_id = models.CharField(max_length=200, default='')
    tool_consumer_instance_guid = models.CharField(max_length=200, default='')
    experimental_group = models.ForeignKey(
        ExperimentalGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = (('user_id', 'tool_consumer_instance_guid'),)

    def __str__(self):
        return "Learner: {}/{}".format(
            self.user_id or "<user_id>",
            self.tool_consumer_instance_guid or "<tool_consumer_instance_guid>"
        )


class Score(models.Model):
    """
    Score resulting from a learner's attempt on an activity
    """
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    # score value
    score = models.FloatField()
    # creation time
    timestamp = models.DateTimeField(null=True, auto_now_add=True)

    def __str__(self):
        return "Score: {} [{} - {}]".format(
            self.score, self.learner, self.activity)


class Transit(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "Transit: {} [{} - {}]".format(
            self.value, self.activity, self.knowledge_component)


class Guess(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "Guess: {} [{} - {}]".format(
            self.value, self.activity, self.knowledge_component)


class Slip(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "Slip: {} [{} - {}]".format(
            self.value, self.activity, self.knowledge_component)


class Mastery(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "Mastery: {} [{} - {}]".format(
            self.value, self.learner, self.knowledge_component)


class Exposure(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.IntegerField()

    def __str__(self):
        return "Exposure: {} [{} - {}]".format(
            self.value, self.learner, self.knowledge_component)


class Confidence(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return "Confidence: {} [{} - {}]".format(
            self.value, self.learner, self.knowledge_component)


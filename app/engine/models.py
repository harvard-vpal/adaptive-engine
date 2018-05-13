# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Collection(models.Model):
    """
    Collection consists of multiple activities
    """
    name = models.CharField(max_length=200)
    max_problems = models.PositiveIntegerField(null=True, blank=True)

    def __unicode__(self):
        return "{} - {}".format(self.pk, self.name)

    def grade(self, learner):
        """
        Generate learner grade based on masteries that bridge can query
        as a grading policy option. 
        Just uses a placeholder value for now
        """
        return 0.5


class KnowledgeComponent(models.Model):
    name = models.CharField(max_length=200)
    mastery_prior = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return "{} - {}".format(self.pk, self.name)


class PrerequisiteRelation(models.Model):
    prerequisite = models.ForeignKey(
        KnowledgeComponent,
        on_delete=models.CASCADE,
        related_name="dependent_relation"
    )
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "KC {} -> KC {} = {}".format(
            self.prerequisite.pk,
            self.knowledge_component.pk,
            self.value
        )


class Activity(models.Model):
    """
    Activity model
    """
    url = models.CharField(max_length=500, default='')
    name = models.CharField(max_length=200, default='')
    collections = models.ManyToManyField(Collection,blank=True)
    knowledge_components = models.ManyToManyField(KnowledgeComponent, blank=True)
    difficulty = models.FloatField(null=True,blank=True)
    tags = models.TextField(default='', blank=True)
    type = models.CharField(max_length=200, default='')
    # whether to include as valid problem to recommend from adaptive engine
    include_adaptive = models.BooleanField(default=True)
    # order for non-adaptive problems
    nonadaptive_order = models.PositiveIntegerField(null=True, blank=True)
    # order for pre-adaptive problems
    preadaptive_order = models.PositiveIntegerField(null=True, blank=True)

    def __unicode__(self):
        return "{} - {}".format(self.pk, self.name)


class EngineSettings(models.Model):
    name = models.CharField(max_length=200, default='')
    r_star = models.FloatField()  # Threshold for forgiving lower odds of mastering pre-requisite LOs.
    L_star = models.FloatField()  # Threshold logarithmic odds. If mastery logarithmic odds are >= than L_star, the LO is considered mastered
    W_p = models.FloatField()  # Importance of readiness in recommending the next item
    W_r = models.FloatField()  # Importance of demand in recommending the next item
    W_c = models.FloatField()  # Importance of continuity in recommending the next item
    W_d = models.FloatField()  # Importance of appropriate difficulty in recommending the next item

    def __unicode__(self):
        return "{} - {}".format(self.pk, self.name)


class ExperimentalGroup(models.Model):
    name = models.CharField(max_length=200,default='')
    weight = models.FloatField(default=0)
    engine_settings = models.ForeignKey(
        EngineSettings,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __unicode__(self):
        return "{} - {}".format(self.pk, self.name) 

#TODO Course model?


class Learner(models.Model):
    """
    User model for students
    """
    lti_user_id = models.CharField(max_length=200, default='')
    experimental_group = models.ForeignKey(
            ExperimentalGroup,
            on_delete=models.SET_NULL,
            null=True
    )

    def __unicode__(self):
        return "{}".format(self.pk)


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

    def __unicode__(self):
        return "Learner {} - Activity {} = {}".format(
            self.learner.pk, self.activity.pk, self.score)


class Transit(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "Activity {} - KC {} = {}".format(
            self.activity.pk, self.knowledge_component.pk, self.value)


class Guess(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "Activity {} - KC {} = {}".format(
            self.activity.pk, self.knowledge_component.pk, self.value)


class Slip(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "Activity {} - KC {} = {}".format(
            self.activity.pk, self.knowledge_component.pk, self.value)


class Mastery(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "Learner {} - KC {} = {}".format(
            self.learner.pk, self.knowledge_component.pk, self.value)


class Exposure(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.IntegerField()

    def __unicode__(self):
        return "Learner {} - KC {} = {}".format(
            self.learner.pk, self.knowledge_component.pk, self.value)


class Confidence(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    knowledge_component = models.ForeignKey(KnowledgeComponent, on_delete=models.CASCADE)
    value = models.FloatField()

    def __unicode__(self):
        return "Learner {} - KC {} = {}".format(
            self.learner.pk, self.knowledge_component.pk, self.value)


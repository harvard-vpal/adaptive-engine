# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Collection(models.Model):
    """
    Collection consists of multiple activities
    """
    name = models.CharField(max_length=200)

    def recommend(self,learner):
        """
        Recommend and return an activity from this collection for a particular learner
        """
        # simple example
        activity = self.activity_set.first()

        return activity


class KnowledgeComponent(models.Model):
    name = models.CharField(max_length=200)


class PrerequisiteRelation(models.Model):
    prerequisite = models.ForeignKey(KnowledgeComponent, 
        related_name="dependent_relation"
    )
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()


class Activity(models.Model):
    """
    Activity model
    """
    name = models.CharField(max_length=200)
    collections = models.ManyToManyField(Collection)
    knowledge_components = models.ManyToManyField(KnowledgeComponent,blank=True)


# class Course(models.Model):
#     """
#     Course from which a learner can come from
#     """
#     name = models.CharField(max_length=200)


class Learner(models.Model):
    """
    User model for students
    """
    # course = models.ForeignKey(Course)
    identifier = models.PositiveIntegerField(unique=True) #maybe int?

    # class Meta:
    #     unique_together = ('course','identifier')


class Score(models.Model):
    """
    Score resulting from a learner's attempt on an activity
    """
    learner = models.ForeignKey(Learner)
    activity = models.ForeignKey(Activity)
    score = models.FloatField()
    # timestamp


# class TagGroup(models.Model):
#     """
#     Tag grouping
#     """
#     name = models.CharField(max_length=200)


# class TagLabel(models.Model):
#     """
#     Tag label
#     """
#     name = models.CharField(max_length=200)
#     tag_group = models.ForeignKey(TagGroup)

# class Tag(models.Model):
#     """
#     Tagging on an activity
#     """
#     activity = models.ForeignKey(Activity)
#     tag_label = models.ForeignKey(TagLabel)

# class KnowledgeComponentTag(models.Model):
#     knowledge_component = models.ForeignKey(KnowledgeComponent)
#     activity = models.ForeignKey(Activity)

# class Difficulty(models.Model):
#     prerequisite = models.ForeignKey(KnowledgeComponent)
#     value = models.FloatField()


class Difficulty(models.Model):
    activity = models.ForeignKey(Activity)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

class Guess(models.Model):
    activity = models.ForeignKey(Activity)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

class Slip(models.Model):
    activity = models.ForeignKey(Activity)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

class Transfer(models.Model):
    activity = models.ForeignKey(Activity)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

# class InitialMastery(models.Model):
#     learner = models.ForeignKey(Learner)
#     knowledge_component = models.ForeignKey(KnowledgeComponent)
#     value = models.FloatField()

class Mastery(models.Model):
    learner = models.ForeignKey(Learner)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

class Exposure(models.Model):
    learner = models.ForeignKey(Learner)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.IntegerField()

class Confidence(models.Model):
    learner = models.ForeignKey(Learner)
    knowledge_component = models.ForeignKey(KnowledgeComponent)
    value = models.FloatField()

# class LastSeen(models.Model):
#     """
#     could be replace with score data lookup
#     """
#     learner = models.ForeignKey(Learner)
#     value = models.IntegerField()

# class Unseen(models.Model):
#     learner = models.ForeignKey(Learner)
#     activity = models.ForeignKey(Activity)
#     value = models.BooleanField(default=True)


class EngineSettings(models.Model):
    name = models.CharField(max_length=200)
    epsilon = models.FloatField()
    eta = models.FloatField()
    M = models.FloatField()
    r_star = models.FloatField()
    L_star = models.FloatField()
    W_p = models.FloatField()
    W_r = models.FloatField()
    W_c = models.FloatField()
    W_d = models.FloatField()
    slip_probability = models.FloatField()
    guess_probability = models.FloatField()
    trans_probability = models.FloatField()
    prior_knowledge_probability = models.FloatField()
    stop_on_mastery = models.BooleanField()




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

class Activity(models.Model):
    """
    Activity model
    """
    name = models.CharField(max_length=200)
    collection = models.ManyToManyField(Collection)


class Course(models.Model):
    """
    Course from which a learner can come from
    """
    name = models.CharField(max_length=200)


class Learner(models.Model):
    """
    User model for students
    """
    course = models.ForeignKey(Course)
    identifier = models.PositiveIntegerField() #maybe int?

    class Meta:
        unique_together = ('course','identifier')


class Score(models.Model):
    """
    Score resulting from a learner's attempt on an activity
    """
    learner = models.ForeignKey(Learner)
    activity = models.ForeignKey(Activity)
    score = models.FloatField()


class TagGroup(models.Model):
    """
    Tag grouping
    """
    name = models.CharField(max_length=200)


class TagLabel(models.Model):
    """
    Tag label
    """
    name = models.CharField(max_length=200)
    tag_group = models.ForeignKey(TagGroup)


class Tag(models.Model):
    """
    Tagging on an activity
    """
    activity = models.ForeignKey(Activity)
    tag_label = models.ForeignKey(TagLabel)

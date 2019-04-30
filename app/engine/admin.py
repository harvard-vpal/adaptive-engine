# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *


class ActivityInline(admin.TabularInline):
    model = Collection.activity_set.through
    readonly_fields = ['activity']


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    inlines = [
        ActivityInline
    ]


admin.site.register(Activity)
admin.site.register(Learner)
admin.site.register(Score)
admin.site.register(KnowledgeComponent)
admin.site.register(EngineSettings)
admin.site.register(ExperimentalGroup)
admin.site.register(PrerequisiteRelation)
admin.site.register(Guess)
admin.site.register(Slip)
admin.site.register(Transit)
admin.site.register(Mastery)

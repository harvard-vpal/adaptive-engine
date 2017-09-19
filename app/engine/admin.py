# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *


admin.site.register(Collection)
admin.site.register(Activity)
admin.site.register(Learner)
admin.site.register(Score)
admin.site.register(KnowledgeComponent)
admin.site.register(EngineSettings)

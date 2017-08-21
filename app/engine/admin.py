# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Collection)
admin.site.register(Activity)
admin.site.register(Tag)
admin.site.register(TagGroup)
admin.site.register(TagLabel)
admin.site.register(Course)
admin.site.register(Learner)
admin.site.register(Score)

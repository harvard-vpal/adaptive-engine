from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^engine/', include('engine.urls', namespace="engine")),
    url(r'^admin/', include(admin.site.urls)),
]

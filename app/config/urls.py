from django.urls import include, path
from django.contrib import admin
from . import views

urlpatterns = [
    path('engine/', include('engine.urls', namespace="engine")),
    path('admin/', admin.site.urls),
    path('health/', views.health),
]

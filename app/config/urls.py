from django.urls import include, path
from django.contrib import admin
from config import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', views.health),
    path('', include('engine.urls', namespace="engine")),
]

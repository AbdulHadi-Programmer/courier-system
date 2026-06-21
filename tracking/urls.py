from django.urls import path

from . import views

app_name = 'tracking'

urlpatterns = [
    path('', views.track_shipment, name='track'),
    path('progress/<int:pk>/', views.auto_progress, name='progress'),
    path('complete/<int:pk>/', views.auto_complete, name='complete'),
]

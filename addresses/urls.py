from django.urls import path
from . import views

app_name = 'addresses'

urlpatterns = [
    path('', views.address_list, name='list'),
    path('<int:pk>/delete/', views.address_delete, name='delete'),
    path('api/', views.address_api, name='api'),
]

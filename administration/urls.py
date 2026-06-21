from django.urls import path

from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('shipments/', views.shipment_management, name='shipment_management'),
    path('shipments/<int:pk>/delete/', views.admin_delete_shipment, name='delete_shipment'),
]

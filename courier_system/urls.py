from django.contrib import admin
from django.urls import path, include

admin.site.site_header = 'QuickShip Admin'
admin.site.site_title = 'QuickShip Admin'
admin.site.index_title = 'System Management'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('shipments/', include('shipments.urls')),
    path('tracking/', include('tracking.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('administration/', include('administration.urls')),
    path('addresses/', include('addresses.urls')),
    path('chatbot/', include('chatbot.urls')),
]

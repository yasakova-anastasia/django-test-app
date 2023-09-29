from django.contrib import admin
from dj_rest_auth.views import LoginView, LogoutView
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(
        permission_classes=[]
    ), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(
        url_name='schema',
        permission_classes=[]
    ), name='swagger'),
    path('api/docs/', SpectacularRedocView.as_view(
        url_name='schema',
        permission_classes=[]
    ), name='redoc'),
]

from dj_rest_auth.views import LoginView, LogoutView
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework_nested import routers

from . import views

cross_router = routers.SimpleRouter()
cross_router.register(r'crosses', views.CrossViewSet)
cross_router.register(r'tasks', views.TaskViewSet)

urlpatterns = [
    path('', include(cross_router.urls)),
    path('schema/', SpectacularAPIView.as_view(
        permission_classes=[]
    ), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(
        url_name='schema',
        permission_classes=[]
    ), name='swagger'),
    path('docs/', SpectacularRedocView.as_view(
        url_name='schema',
        permission_classes=[]
    ), name='redoc'),
    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
]

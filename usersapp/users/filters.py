import django_filters
from django.contrib.auth.models import User


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['exact'],
            'email': ['exact'],
            'first_name': ['exact'],
            'last_name': ['exact'],
        }
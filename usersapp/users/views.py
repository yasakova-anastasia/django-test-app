from django.contrib.auth.models import User
from django_filters import rest_framework
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from .filters import UserFilter
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (rest_framework.DjangoFilterBackend, filters.OrderingFilter,)
    filterset_class = UserFilter
    ordering_fields = '__all__'


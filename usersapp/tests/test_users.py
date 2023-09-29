import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def authenticated_client():
    user = User.objects.create_user(username='testuser', password='testpassword')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_create_user(authenticated_client):
    client = authenticated_client

    user_data = {'username': 'newuser', 'password': 'newpassword', 'email': 'new@example.com'}
    response = client.post(reverse('user-list'), user_data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_get_user(authenticated_client):
    client = authenticated_client

    user = User.objects.create_user(username='testuser1', password='testpassword1', email='test1@example.com')
    response = client.get(reverse('user-detail', args=[user.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == 'testuser1'


@pytest.mark.django_db
def test_delete_user(authenticated_client):
    client = authenticated_client

    user = User.objects.create_user(username='user_to_delete', password='testpassword', email='delete@example.com')
    response = client.delete(reverse('user-detail', args=[user.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(username='user_to_delete').exists()


@pytest.mark.django_db
def test_get_multiple_users(authenticated_client):
    client = authenticated_client

    User.objects.create_user(username='user1', password='testpassword1', email='user1@example.com')
    User.objects.create_user(username='user2', password='testpassword2', email='user2@example.com')
    User.objects.create_user(username='user3', password='testpassword3', email='user3@example.com')

    response = client.get(reverse('user-list'))

    assert response.status_code == status.HTTP_200_OK

    usernames = [user['username'] for user in response.data]
    assert 'user1' in usernames
    assert 'user2' in usernames
    assert 'user3' in usernames


@pytest.mark.django_db
def test_sort_users(authenticated_client):
    client = authenticated_client

    User.objects.create_user(username='b', password='testpassword1', email='b@example.com')
    User.objects.create_user(username='a', password='testpassword2', email='a@example.com')
    User.objects.create_user(username='c', password='testpassword3', email='c@example.com')

    response = client.get(reverse('user-list') + '?ordering=username')

    assert response.status_code == status.HTTP_200_OK

    usernames = [user['username'] for user in response.data]
    assert usernames == ['a', 'b', 'c', 'testuser']


@pytest.mark.django_db
def test_filter_users(authenticated_client):
    client = authenticated_client

    User.objects.create_user(username='user1', password='testpassword1', email='user1@example.com')
    User.objects.create_user(username='user2', password='testpassword2', email='user2@example.com')
    User.objects.create_user(username='user3', password='testpassword3', email='user3@example.com')

    response = client.get(reverse('user-list') + '?email=user2@example.com')

    assert response.status_code == status.HTTP_200_OK

    assert len(response.data) == 1
    assert response.data[0]['username'] == 'user2'


@pytest.mark.django_db
def test_update_user(authenticated_client):
    client = authenticated_client

    user = User.objects.create_user(username='user_to_update', password='testpassword', email='update@example.com')

    updated_data = {
        'username': 'newusername',
        'email': 'newemail@example.com',
    }

    url = reverse('user-detail', args=[user.id])
    response = client.put(url, updated_data, format='json')

    assert response.status_code == status.HTTP_200_OK

    user.refresh_from_db()
    assert user.username == updated_data['username']
    assert user.email == updated_data['email']

from enum import Enum

from django.contrib.auth.models import User
from django.db import models


class StatusChoice(str, Enum):
    CREATED = 'created'
    STARTED = 'started'
    FINISHED = 'finished'

    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)

    @classmethod
    def list(cls):
        return list(map(lambda x: x.value, cls))

    def __str__(self):
        return self.value


class Cross(models.Model):
    start_time = models.DateTimeField(default=None, null=True)
    end_time = models.DateTimeField(default=None, null=True)
    status = models.CharField(max_length=255, choices=StatusChoice.choices(),
        default=StatusChoice.CREATED)

    class Meta:
        default_permissions = ()

class Task(models.Model):
    cross = models.ForeignKey(Cross, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    coordinates = models.CharField(max_length=255)
    description = models.CharField(max_length=300)
    correct_answer = models.CharField(max_length=255)
    hint1 = models.CharField(max_length=300)
    hint2 = models.CharField(max_length=300)
    hint3 = models.CharField(max_length=300)

    class Meta:
        default_permissions = ()

class HintTaken(models.Model):
    hint_number = models.IntegerField(default=0)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    team = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=['task', 'team'], name='unique_hint_taken')
        ]

class Answer(models.Model):
    team = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    answer = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()

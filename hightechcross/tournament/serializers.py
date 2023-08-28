from django.db import transaction
from rest_framework import serializers

from .models import Answer, Cross, HintTaken, StatusChoice, Task


class TaskSerializer(serializers.ModelSerializer):
    cross = serializers.ReadOnlyField(source="cross.id")
    name = serializers.CharField(max_length=255, required=True)
    coordinates = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(max_length=300, required=True)
    correct_answer = serializers.CharField(max_length=255, required=True)
    hint1 = serializers.CharField(max_length=300, required=True)
    hint2 = serializers.CharField(max_length=300, required=True)
    hint3 = serializers.CharField(max_length=300, required=True)

    class Meta:
        model = Task
        fields = '__all__'


class CrossSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, required=True)
    start_time = serializers.DateTimeField(default=None, read_only=True)
    end_time = serializers.DateTimeField(default=None, read_only=True)
    status = serializers.ChoiceField(choices=StatusChoice.choices(),
                                     default=StatusChoice.CREATED,
                                     read_only=True)

    class Meta:
        model = Cross
        fields = '__all__'
        read_only_fields = ['start_time', 'end_time', 'status']

    @transaction.atomic
    def create(self, validated_data):
        tasks = validated_data.pop('tasks', [])
        db_cross = Cross.objects.create(**validated_data)

        for task in tasks:
            Task.objects.create(**task, cross=db_cross)

        db_cross.save()
        return db_cross


class AnswerSerializer(serializers.ModelSerializer):
    answer = serializers.CharField(max_length=255, required=True)
    submitted_at = serializers.DateTimeField()
    is_correct = serializers.BooleanField(required=True)

    class Meta:
        model = Answer
        fields = '__all__'


class HintTakenSerializer(serializers.ModelSerializer):
    hint_number = serializers.IntegerField(allow_null=True, required=True)
    task = serializers.ReadOnlyField(source="task.id")
    team = serializers.ReadOnlyField(source="team.id")

    class Meta:
        model = HintTaken
        fields = '__all__'

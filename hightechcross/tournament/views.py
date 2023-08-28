import datetime

import pytz
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiParameter, extend_schema,
                                   extend_schema_view)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Answer, Cross, HintTaken, StatusChoice, Task, User
from .serializers import AnswerSerializer, CrossSerializer


@extend_schema(tags=["crosses"])
@extend_schema_view(
    retrieve=extend_schema(
        summary="Method returns details of a cross",
        responses={"200": CrossSerializer},
    ),
    list=extend_schema(
        summary="Method returns a paginated list of crosses",
        responses={"200": CrossSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Method creates a cross",
        responses={ "201": CrossSerializer}
    ),
    start=extend_schema(
        summary="Method starts a cross",
    ),
)
class CrossViewSet(viewsets.ModelViewSet):
    queryset = Cross.objects.all()
    serializer_class = CrossSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "delete"]

    @extend_schema(
        methods=["POST"],
        operation_id="crosses_start",
        summary="Method starts a cross",
        request=None
    )
    @action(detail=True,
        methods=["POST"],
        url_path='start',
    )
    def start(self, request, pk):
        try:
            db_cross = Cross.objects.get(pk=pk)
        except Cross.DoesNotExist:
            return Response(data={"detail": "Cross not found"}, status=status.HTTP_404_NOT_FOUND)

        if db_cross.status == StatusChoice.FINISHED:
            return Response(data={"detail": "Cross have already finished. You cannot start it again"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

        if Cross.objects.filter(status=StatusChoice.STARTED):
            return Response(data={"detail": "Some cross have already started"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)

        start_time = datetime.datetime.now(tz=pytz.utc)
        db_cross.start_time = start_time
        db_cross.end_time = start_time + datetime.timedelta(minutes=20)
        db_cross.status = StatusChoice.STARTED
        db_cross.save()

        return Response(data=CrossSerializer(db_cross).data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["GET"],
        summary="Get results of all teams",
        operation_id="crosses_list_results"
    )
    @action(detail=True, methods=["GET"], url_path="results")
    def results(self, request, pk):
        try:
            db_cross = Cross.objects.get(pk=pk)
        except Cross.DoesNotExist:
            return Response(data={"detail": "Cross not found"}, status=status.HTTP_404_NOT_FOUND)

        if db_cross.status == StatusChoice.CREATED:
            return Response(data={"detail": "Cross not started"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        if db_cross.status == StatusChoice.STARTED and datetime.datetime.now(tz=pytz.utc) > db_cross.end_time:
            db_cross.status = StatusChoice.FINISHED
            db_cross.save()

        results = []
        db_users = User.objects.filter(groups__name='user')
        db_tasks = Task.objects.filter(cross=db_cross)
        for db_user in db_users:
            tasks = []
            completed_tasks = 0
            penalty_time = datetime.timedelta()
            for db_task in db_tasks:
                try:
                    db_answer = Answer.objects.get(task=db_task, team=db_user, is_correct=True)
                    task_status = True

                    completed_tasks += 1

                    penalty_time += (db_answer.submitted_at - db_task.cross.start_time)

                    try:
                        db_hint_taken = HintTaken.objects.get(team=request.user, task=db_task)
                        hint_number = db_hint_taken.hint_number
                    except HintTaken.DoesNotExist:
                        hint_number = 0

                    penalty_time += (datetime.timedelta(minutes=15) * hint_number)

                    wrong_answers = Answer.objects.filter(team=db_user, task=db_task, is_correct=False).count()
                    penalty_time += (datetime.timedelta(minutes=30) * wrong_answers)

                except Answer.DoesNotExist:
                    task_status = False

                tasks.append({
                    "name": db_task.name,
                    "status": task_status
                })

            results.append({
                "team": db_user.username,
                "completed_tasks": completed_tasks,
                "penalty_time": penalty_time,
                "tasks": tasks
            })

        return Response(data=results, status=status.HTTP_200_OK)


@extend_schema(tags=["tasks"])
@extend_schema_view(
    list=extend_schema(
        summary="Get a list of all tasks of current cross",
    ),
    submit=extend_schema(
        summary="Submit an answer to a task",
    ),
    hints=extend_schema(
        summary="Open the hint",
    ),
)
class TaskViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.all()
    serializer_class = CrossSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        methods=["GET"],
        operation_id="tasks",
        summary="Method returns a list of all tasks of current cross",
    )
    def list(self, request):
        try:
            db_cross = Cross.objects.get(status=StatusChoice.STARTED)
        except Cross.DoesNotExist:
            return Response(data={"detail": "Cross not started"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        db_tasks = Task.objects.filter(cross=db_cross)

        tasks = []
        for db_task in db_tasks:
            try:
                db_hint_taken = HintTaken.objects.get(team=request.user, task=db_task)
                hint_number = db_hint_taken.hint_number
            except HintTaken.DoesNotExist:
                hint_number = 0

            hints = []
            if hint_number > 0:
                hints.append(db_task.hint1)
            if hint_number > 1:
                hints.append(db_task.hint2)
            if hint_number > 2:
                hints.append(db_task.hint3)

            answer_status = "not started"
            db_answers = Answer.objects.filter(task=db_task, team=request.user)
            if db_answers.exists():
                try:
                    db_answers.get(is_correct=True)
                    answer_status = "correct"
                except Answer.DoesNotExist:
                    answer_status = "wrong"

            tasks.append({
                "id": db_task.id,
                "name": db_task.name,
                "coordinates": db_task.coordinates,
                "description": db_task.description,
                "hints": hints,
                "status": answer_status
            })

        return Response(data=tasks, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["POST"],
        operation_id="tasks_submit",
        summary="Submit an answer to a task",
        parameters=[
            OpenApiParameter('answer', location=OpenApiParameter.QUERY, type=OpenApiTypes.STR, required=True),
        ],
        request=None,
    )
    @action(detail=True,
        methods=["POST"],
        url_path='submit',
    )
    def submit(self, request, pk):
        answer = request.query_params.get("answer")
        try:
            db_task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response(data={"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        if db_task.cross.status != StatusChoice.STARTED:
            return Response(data={"detail": "Cross not started"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        if datetime.datetime.now(tz=pytz.utc) > db_task.cross.end_time:
            return Response(data={"detail": "Cross finished"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            db_answer = Answer.objects.get(task=db_task, team=request.user, answer=answer)
        except Answer.DoesNotExist:
            is_correct = False
            if answer == db_task.correct_answer:
                is_correct = True
            db_answer = Answer.objects.create(team=request.user, task=db_task, answer=answer, is_correct=is_correct)

        return Response(data=AnswerSerializer(db_answer).data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["POST"],
        operation_id="tasks_hints",
        summary="Open the hint",
        parameters=[
            OpenApiParameter('hint_number', location=OpenApiParameter.PATH, type=OpenApiTypes.NUMBER, required=True),
        ],
        request=None
    )
    @action(detail=True,
        methods=["POST"],
        url_path=r"hints/(?P<hint_number>\S+)"
    )
    def hints(self, request, pk, hint_number):
        hint_number = int(hint_number)
        if hint_number not in [0, 1, 2]:
            return Response(data={"detail": "Hint number should be in [0, 1, 2]"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            db_task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response(data={"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        if db_task.cross.status != StatusChoice.STARTED:
            return Response(data={"detail": "Cross not started"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        try:
            db_hint_taken = HintTaken.objects.get(team=request.user, task=db_task)
        except HintTaken.DoesNotExist:
            db_hint_taken = HintTaken.objects.create(hint_number=0, team=request.user, task=db_task)

        if hint_number > db_hint_taken.hint_number:
            return Response(data={"detail": f"Firstly you should open the {db_hint_taken.hint_number} hint"},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        hint = ""
        if hint_number == 0:
            if db_hint_taken.hint_number < 1:
                db_hint_taken.hint_number = 1
            hint = db_task.hint1

        elif hint_number == 1:
            if db_hint_taken.hint_number < 2:
                db_hint_taken.hint_number = 2
            hint = db_task.hint2

        elif hint_number == 2:
            if db_hint_taken.hint_number < 3:
                db_hint_taken.hint_number = 3
            hint = db_task.hint3

        db_hint_taken.save()

        return Response(data={"hint": hint}, status=status.HTTP_200_OK)

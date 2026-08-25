from html.parser import incomplete
from typing import Iterable, Iterator

from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    Model,
)
from django.db.transaction import atomic


class GoalTaskFields(Model):

    class Meta:
        abstract = True

    name = CharField(max_length=30)
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)
    position = IntegerField(null=True, blank=True)


class Goal(GoalTaskFields):

    def get_goals_and_tasks(self) -> Iterator[tuple["Goal", list["Task"]]]:
        incomplete_goals = Goal.objects.filter(completed_at__isnull=True)
        remaining_goals = incomplete_goals.count()


        goals = incomplete_goals.prefetch_related('tasks').order_by('position')
        for goal in goals:

            yield goal, goal.tasks.filter().order_by('position')


class Task(GoalTaskFields):

    goal = ForeignKey(
        Goal,
        on_delete=CASCADE,
        related_name='tasks',
    )

    def move_task_position(self, direction: str):
        queryset = Task.objects.filter(completed_at__isnull=True)

        if direction == 'up':
            position_operator, order_by_prefix = 'gt', ''
        else:
            position_operator, order_by_prefix = 'lt', '-'

        other_task = queryset.filter(
            **{f"position__{position_operator}": self.position}
        ).order_by(
            f'{order_by_prefix}position',
        ).first()

        if other_task is None:
            return

        with atomic():
            self.position, other_task.position = (
                other_task.position,
                self.position,
            )
            self.save()
            other_task.save()





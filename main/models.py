
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Iterator

from django.conf import settings
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

    def __str__(self):
        return self.name


@dataclass
class GoalAndTasks:
    goal: 'Goal'
    tasks: list['Task']

    def unpack(self) -> tuple['Goal', list['Task']]:
        return self.goal, self.tasks


class Goal(GoalTaskFields):

    @staticmethod
    def get_goals_and_tasks_to_display() -> list[GoalAndTasks]:

        tasks_by_goal: list[GoalAndTasks] = []

        total_goals: int = 0
        total_tasks: int = 0
        goals_queryset = Goal.objects.filter(
            completed_at__isnull=True,
        ).prefetch_related(
            'tasks'
        ).order_by('position')
        for goal in goals_queryset:
            total_goals += 1
            tasks = list(
                goal.tasks.filter(
                    completed_at__isnull=True,
                ).order_by('position')
            )
            task_count: int = len(tasks)
            total_tasks += task_count
            tasks_by_goal.append(GoalAndTasks(goal, tasks))

        min_tasks_by_index = {0: 3, 1: 2}

        max_tasks_to_display = settings.MAX_TASKS_TO_DISPLAY
        if total_goals >= max_tasks_to_display:
            for i, goal_and_tasks in enumerate(tasks_by_goal):
                limit = min_tasks_by_index.get(i, 1)
                goal_and_tasks.tasks = goal_and_tasks.tasks[:limit]
            return tasks_by_goal

        if total_tasks <= max_tasks_to_display:
            return tasks_by_goal

        tasks_by_goal_len = len(tasks_by_goal)
        for forward_index in range(tasks_by_goal_len):
            reverse_index = (tasks_by_goal_len - 1) - forward_index
            goal_and_tasks = tasks_by_goal[reverse_index]
            min_tasks_for_goal = min_tasks_by_index.get(reverse_index, 1)
            num_tasks_for_goal = len(goal_and_tasks.tasks)
            number_to_remove = num_tasks_for_goal - min_tasks_for_goal
            if number_to_remove < 1:
                # We cannot remove any tasks from this goal
                continue
            # If we can get down to max_tasks_to_display by removing tasks
            # from this Goal.  Only remove enough tasks to do so.
            number_to_remove = min(
                number_to_remove,
                total_tasks - max_tasks_to_display,
            )
            goal_and_tasks.tasks = goal_and_tasks.tasks[:-number_to_remove]
            total_tasks -= number_to_remove
            if total_tasks <= max_tasks_to_display:
                break

        return tasks_by_goal


class Task(GoalTaskFields):

    class Meta:
        unique_together = ('goal', 'position')

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






from typing import Iterable, Iterator

from django.conf import settings
from django.db.models import Model
from django.test import TestCase

from main.models import Goal, GoalAndTasks, Task
from main.settings import MAX_TASKS_TO_DISPLAY


class GoalTest(TestCase):

    @staticmethod
    def build_tasks_and_goals(tasks_per_goal: list[int]) -> list[GoalAndTasks]:
        list_out: list[GoalAndTasks] = []
        for i, task_count in enumerate(tasks_per_goal, 1):
            goal_name = str(i)
            goal: Goal = Goal.objects.create(
                name=goal_name,
                position=i,
            )
            tasks: list[Task] = [
                Task.objects.create(
                    name=f'{goal_name}-{j}',
                    goal=goal,
                    position=j,
                )
                for j in range(1, task_count + 1)
            ]
            list_out.append(GoalAndTasks(goal=goal, tasks=tasks))
        return list_out

    @staticmethod
    def build_expected(
            list_in: list[GoalAndTasks],
            num_selected_per_goal: list[int],
    ) -> list[GoalAndTasks]:
        in_length = len(list_in)
        mask_length = len(num_selected_per_goal)
        if in_length != mask_length:
            raise ValueError(
                f'Length of list_in ({in_length}) and selected_per_goal '
                f'({mask_length}) must be equal'
            )
        return [
            GoalAndTasks(item.goal, item.tasks[:num_selected])
            for item, num_selected in zip(
                list_in,
                num_selected_per_goal,
            )
        ]

    def test_get_goals_and_tasks_to_display__no__goals(self):
        self.assertEqual([], Goal.get_goals_and_tasks_to_display())

    def test_get_goals_and_tasks_to_display__num_goals_exceeds_limit(self):
        expected: list[GoalAndTasks] = self.build_expected(
            self.build_tasks_and_goals([4, 3, 2, 2, 2, 2]),
            num_selected_per_goal=[3, 2, 1, 1, 1, 1],
        )
        with self.settings(MAX_TASKS_TO_DISPLAY=5):
            self.assertEqual(expected, Goal.get_goals_and_tasks_to_display())

    def test_get_goals_and_tasks_to_display__at_or_under_limit(self):
        expected: list[GoalAndTasks] = self.build_expected(
            self.build_tasks_and_goals([4, 3, 2]),
            num_selected_per_goal=[4, 3, 2],
        )
        with self.settings(MAX_TASKS_TO_DISPLAY=10):
            self.assertEqual(expected, Goal.get_goals_and_tasks_to_display())

    def test_get_goals_and_tasks_to_display__over_limit_hit_min_tasks_per_goal(self):
        expected: list[GoalAndTasks] = self.build_expected(
            self.build_tasks_and_goals([4, 4, 2, 3, 4]),
            num_selected_per_goal=[3, 2, 1, 1, 1],
        )
        with self.settings(MAX_TASKS_TO_DISPLAY=7):
            self.assertEqual(expected, Goal.get_goals_and_tasks_to_display())

    def test_get_goals_and_tasks_to_display__can_trim_down_to_max_tasks_to_display(self):
        expected_list: list[GoalAndTasks] = self.build_expected(
            self.build_tasks_and_goals([4, 2, 3, 3, 4]),
            num_selected_per_goal=[4, 2, 3, 1, 1],
        )
        with self.settings(MAX_TASKS_TO_DISPLAY=11):
            for i, expected_and_actual in enumerate(
                    zip(
                        expected_list,
                        Goal.get_goals_and_tasks_to_display(),
                    )
            ):
                expected, actual = expected_and_actual
                self.assertEqual(expected, actual, f"{i=}")




from django.db.models import (
    CharField,
    DateTimeField,
    IntegerField,
    Model,
)
from django.db.transaction import atomic


class Task(Model):

    name = CharField(max_length=30)
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)
    position = IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'task'
        app_label = 'task_stack'

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
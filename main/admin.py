
from django.contrib.admin import ModelAdmin, register

from main.models import Goal, Task


@register(Goal)
class GoalAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'position', 'completed_at')


@register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ('pk', 'goal', 'name', 'position', 'completed_at')
    list_editable = ('goal', 'name', 'position')

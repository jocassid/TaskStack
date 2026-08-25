#!/usr/bin/env python3

from django import setup
setup()


if True:

    from tkinter import Tk, X, END, messagebox, ttk, font, Label
    from tkinter.constants import LEFT
    from tkinter.messagebox import showwarning
    from typing import Any, Iterable, Optional
    from types import ModuleType

    from django.db import transaction
    from django.db.models import Max
    from django.utils import timezone

    from main.models import Task


class TaskRow:

    def __init__(self, task_grid: 'TaskGrid', task: Task, row: int):
        self.task_grid = task_grid

        self.lbl = Label(
            task_grid,
            text=task.name,
            relief="flat",
            borderwidth=1,
            anchor="w",
            takefocus=1,
        )
        self.lbl.configure(font=font.nametofont("TkDefaultFont"))
        self.lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)

        done_btn = ttk.Button(
            self.task_grid,
            text="✔",
            command=lambda t=task: self.task_grid.complete_task(t)
        )
        done_btn.grid(row=row, column=1, padx=2, pady=2)

        # Move up button
        up_btn = ttk.Button(
            self.task_grid,
            text="↑",
            width=3,
            command=lambda t=task: self.task_grid.move_task(t, "up")
        )
        up_btn.grid(row=row, column=2, padx=2, pady=2)

        # Move down button
        down_btn = ttk.Button(
            self.task_grid,
            text="↓",
            width=3,
            command=lambda t=task: self.task_grid.move_task(t, "down")
        )
        down_btn.grid(row=row, column=3, padx=2, pady=2)

    def highlight(self):
        self.lbl.configure(relief="solid")
        self.lbl.focus_set()

    def unhighlight(self):
        self.lbl.configure(relief="flat")


class TaskGrid(ttk.Frame):
    def __init__(self, app: "TaskStackApp"):
        super().__init__(app.root)
        self.app: "TaskStackApp" = app
        self.columnconfigure(0, weight=1)
        self.rows: list[TaskRow] = []
        self.selection_index = -1

    def refresh(self, tasks: Iterable[Task]):
        for widget in self.winfo_children():
            widget.destroy()
        self.rows.clear()

        for row, task in enumerate(tasks):
            self.rows.append(
                TaskRow(
                    self,
                    task,
                    row,
                ),
            )

    def complete_task(self, task: Task):
        task.completed_at = timezone.now()
        task.save()
        self.refresh_list()

    def move_task(self, task: Task, direction):
        task.move_task_position(direction)
        self.refresh_list()



    def add_task(self, name: str):
        max_position = Task.objects.aggregate(Max('position'))['position__max']
        new_position = (max_position + 1) if max_position is not None else 1
        Task.objects.create(name=name, position=new_position)

    def get_top_tasks(self, limit=5) -> list[Task]:
        return list(Task.objects.filter(completed_at__isnull=True).order_by('-position')[:limit])

    def refresh_list(self):
        tasks = self.get_top_tasks(5)
        self.refresh(tasks)
        self.selection_index = -1
        self.update_selection()

    def update_selection(self) -> None:
        num_tasks = len(self.rows)

        # Unhighlight all tasks
        for row in self.rows:
            row.unhighlight()

        if self.selection_index == -1:
            self.app.focus_new_task_description()
            return

        if self.selection_index >= num_tasks:
            raise ValueError(f"Invalid selection index: {self.selection_index}")

        self.rows[self.selection_index].highlight()

    def navigate_up(self, event=None):
        num_tasks = len(self.rows)
        if num_tasks == 0:
            self.selection_index = -1
        else:
            self.selection_index -= 1
            if self.selection_index < -1:
                self.selection_index = num_tasks - 1
        self.update_selection()

    def navigate_down(self, event=None):
        num_tasks = len(self.rows)
        if num_tasks == 0:
            self.selection_index = -1
        else:
            self.selection_index += 1
            if self.selection_index >= num_tasks:
                self.selection_index = -1
        self.update_selection()


class TaskStackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Stack")

        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(pady=5)

        self.new_task_description = ttk.Entry(self.input_frame, width=30)
        self.new_task_description.pack(side=LEFT, padx=5)
        self.new_task_description.bind("<Return>", lambda e: self.add_task())
        
        self.new_task_button = ttk.Button(
            self.input_frame,
            text="New task",
            command=self.add_task,
        )
        self.new_task_button.pack(side=LEFT, padx=5)

        self.tasks_grid = TaskGrid(self)
        self.tasks_grid.pack(pady=5, padx=10, fill=X)

        self.root.bind_all("<Control-t>", self.focus_new_task)
        self.root.bind_all("<Up>", self.tasks_grid.navigate_up)
        self.root.bind_all("<Down>", self.tasks_grid.navigate_down)
        
        self.tasks_grid.refresh_list()

    def add_task(self):
        """pulls name from new_task_description then calls TaskGrid.add_task"""
        name = self.new_task_description.get()
        if not name.strip():
            return
        self.tasks_grid.add_task(name)
        self.new_task_description.delete(0, END)
        self.tasks_grid.refresh_list()

    def focus_new_task(self, event=None):
        self.selection_index = -1
        self.update_selection()

    def focus_new_task_description(self) -> None:
        self.new_task_description.focus_set()
        self.new_task_description.selection_range(0, END)


def main():
    root = Tk()
    TaskStackApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

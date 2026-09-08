#!/usr/bin/env python3

from django import setup
setup()


if True:
    from platform import system as platform_system

    from tkinter import Menu, Tk
    from tkinter.constants import LEFT
    from tkinter.ttk import Entry, Frame, Treeview

    from main.models import Goal


class InputFrame(Frame):
    def __init__(self, app_window: 'TaskStackApp2'):
        super().__init__(app_window)
        self.app_window = app_window

        self.new_task_description = Entry(self, width=30)
        self.new_task_description.pack(side=LEFT, padx=5)
        self.new_task_description.bind(
            "<Return>",
            lambda e: app_window.add_task(
                self.new_task_description.get()
            ),
        )


class GoalsAndTasksFrame(Frame):
    def __init__(self, app_window: 'TaskStackApp2'):
        super().__init__(app_window)
        self.app_window = app_window

        self.tree = Treeview(self, columns=("Goal", "Task"))
        self.tree.pack(fill="both", expand=True)
        self.populate_tree()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        root_node = self.tree.insert(
            parent="",
            index="end",
            text="Goals and Tasks",
            open=True,
        )
        for goal_and_tasks in Goal.get_goals_and_tasks_to_display():
            goal, tasks = goal_and_tasks.unpack()
            goal_node = self.tree.insert(
                parent=root_node,
                index="end",
                text=f"[{goal.position}] {goal.name}",
                open=True,
            )
            print(f"{hasattr(goal_node, '__hash__')=}")
            for task in tasks:
                self.tree.insert(
                    parent=goal_node,
                    index="end",
                    text=f"{task.position}. {task.name}",
                )




class MenuBar(Menu):

    def __init__(self, app_window: 'TaskStackApp2'):
        super().__init__(app_window)
        self.app_window = app_window

        ctrl = 'Command' if platform_system() == 'Darwin' else 'Control'

        file_menu = Menu(self, tearoff=0)
        file_menu.add_command(label="Settings", command=self.app_window.open_settings)
        file_menu.add_command(
            label="Quit",
            accelerator=f"{ctrl}+Q",
            command=self.app_window.quit,
        )
        self.add_cascade(
            label="File",
            accelerator="Alt+f",
            menu=file_menu,
        )

        self.add_command(
            label='Help',
            accelerator=f"Alt+h",
            command=self.app_window.help,
        )


class TaskStackApp2(Tk):

    def __init__(self):
        super().__init__()
        self.title("Task Stack")

        self.menu_bar = MenuBar(self)
        self.config(menu=self.menu_bar)

        self.input_frame = InputFrame(self)
        self.input_frame.pack(pady=5)

        self.goals_and_tasks = GoalsAndTasksFrame(self)
        self.goals_and_tasks.pack(pady=5)

    def open_settings(self):
        print("open_settings()")
        ...

    def quit(self):
        self.destroy()

    def help(self):
        print("help()")
        ...

    def add_task(self, task_description: str):
        print(f"add_task({task_description!r})")
        ...




def main():
    app = TaskStackApp2()
    app.mainloop()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

from datetime import datetime
from sqlite3 import connect as sqlite_connect
from tkinter import Tk, LEFT, X, END, messagebox, ttk, font, Label
from tkinter.messagebox import showwarning
from typing import Iterable, Optional

from sqlalchemy import (
    create_engine,
    DateTime,
    Engine,
    func,
    Integer,
    String,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column, 
    Session,
)


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=True)


class TaskFrame(ttk.Frame):
    def __init__(self, parent, on_complete, on_move):
        super().__init__(parent)
        self.on_complete = on_complete
        self.on_move = on_move
        self.columnconfigure(0, weight=1)
        self.labels = []

    def refresh(self, tasks: Iterable[Task]):
        for widget in self.winfo_children():
            widget.destroy()
        self.labels = []

        for i, task in enumerate(tasks):
            lbl = Label(
                self,
                text=task.name,
                relief="flat",
                borderwidth=1,
                anchor="w",
                takefocus=1,
            )
            lbl.configure(font=font.nametofont("TkDefaultFont"))
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.labels.append(lbl)

            done_btn = ttk.Button(
                self,
                text="✔",
                command=lambda t=task: self.on_complete(t)
            )
            done_btn.grid(row=i, column=1, padx=2, pady=2)

            # Move Up button
            up_btn = ttk.Button(
                self,
                text="↑",
                width=3,
                command=lambda t=task: self.on_move(t, "up")
            )
            up_btn.grid(row=i, column=2, padx=2, pady=2)

            # Move Down button
            down_btn = ttk.Button(
                self,
                text="↓",
                width=3,
                command=lambda tid=task_id: self.on_move(tid, "down")
            )
            down_btn.grid(row=i, column=3, padx=2, pady=2)





class TaskStackApp:
    def __init__(self, root, engine):
        self.root = root
        self.engine = engine

        self.root.title("Task Stack")
        
        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(pady=5)
        
        self.new_task_description = ttk.Entry(self.input_frame, width=30)
        self.new_task_description.pack('left', padx=5)
        self.new_task_description.bind("<Return>", self.add_task)
        
        self.new_task_button = ttk.Button(self.input_frame, text="New task", command=self.add_task)
        self.new_task_button.pack(side=LEFT, padx=5)
        
        self.tasks_frame = TaskFrame(root, self.complete_task, self.move_task)
        self.tasks_frame.pack(pady=5, padx=10, fill=X)
        
        self.selection_index = -1
        self.root.bind_all("<Control-t>", self.focus_new_task)
        self.root.bind_all("<Up>", self.navigate_up)
        self.root.bind_all("<Down>", self.navigate_down)
        
        self.refresh_list()

    def add_task(self, name: str):
        if not name.strip():
            return

        with Session(self.engine) as session:
            max_position: int | None = session.scalar(
                select(func.max(Task.position))
            )
            new_position = (max_position + 1) if max_position is not None else 1

            session.add(Task(name=name, position=new_position))
            session.commit()

    def focus_new_task(self, event=None):
        self.selection_index = -1
        self.update_selection()

    def navigate_down(self, event=None):
        num_tasks = len(self.tasks_frame.labels)
        if num_tasks == 0:
            self.selection_index = -1
        else:
            self.selection_index += 1
            if self.selection_index >= num_tasks:
                self.selection_index = -1
        self.update_selection()

    def navigate_up(self, event=None):
        num_tasks = len(self.tasks_frame.labels)
        if num_tasks == 0:
            self.selection_index = -1
        else:
            self.selection_index -= 1
            if self.selection_index < -1:
                self.selection_index = num_tasks - 1
        self.update_selection()

    def update_selection(self):
        num_tasks = len(self.tasks_frame.labels)
        
        # Unhighlight all tasks
        for lbl in self.tasks_frame.labels:
            lbl.configure(relief="flat")
            
        if self.selection_index == -1:
            self.new_task_description.focus_set()
            self.new_task_description.selection_range(0, END)
        elif 0 <= self.selection_index < num_tasks:
            self.tasks_frame.labels[self.selection_index].configure(relief="solid")
            self.tasks_frame.labels[self.selection_index].focus_set()

    def get_top_tasks(self, limit=5) -> Iterable[Task]:
        with Session(self.engine) as session:
            return session.scalars(
                select(Task)
                .where(Task.completed_at.is_(None))
                .order_by(Task.position.desc())
                .limit(limit)
            )

    def refresh_list(self):
        tasks = self.get_top_tasks(5)
        self.tasks_frame.refresh(tasks)
        self.selection_index = -1
        self.update_selection()

    def complete_task(self, task: Task):
        with Session(self.engine) as session:
            task.completed_at = datetime.now()
            session.commit()
        self.refresh_list()

    def move_task_position(self, current_task: Task, direction: str):
        with Session(self.engine) as session:

            if direction == "up":
                other_task = session.scalars(
                    select(Task)
                    .where(
                        Task.completed_at.is_(None),
                        Task.position > current_task.position,
                    )
                    .order_by(Task.position.asc())
                    .limit(1)
                ).first()
            else:
                other_task = session.scalars(
                    select(Task)
                    .where(
                        Task.completed_at.is_(None),
                        Task.position < current_task.position,
                    )
                    .order_by(Task.position.desc())
                    .limit(1)
                ).first()

            if other_task is None:
                return

            current_task.position, other_task.position = other_task.position, current_task.position
            session.commit()

    def move_task(self, task: Task, direction):
        self.move_task_position(task, direction)
        self.refresh_list()

def main():

    engine: Engine = create_engine("sqlite:///tasks.db", echo=True)
    root = Tk()
    TaskStackApp(root, engine)
    root.mainloop()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from datetime import datetime
from sqlite3 import connect as sqlite_connect
from tkinter import Tk, LEFT, X, END, messagebox, ttk, font, Label
from tkinter.messagebox import showwarning
from typing import Optional

from sqlalchemy import (
    DateTime,
    func,
    Integer,
    String,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from db_migrations import ALL_MIGRATIONS


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=True)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite_connect(self.db_path)
        self.conn.__enter__()

        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.__exit__(exc_type, exc_value, traceback)

    def setup(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                position INTEGER
            )
        """)
        self.conn.commit()

        for migration in ALL_MIGRATIONS:
            migration(self.conn, self.cursor)
            self.conn.commit()

    def add_task(self,name: str):
        if not name.strip():
            return

        # Get the current maximum position to assign the next one
        self.cursor.execute("SELECT MAX(position) FROM tasks")
        max_pos = self.cursor.fetchone()[0]
        new_pos = (max_pos + 1) if max_pos is not None else 1

        self.cursor.execute(
            "INSERT INTO tasks (name, position) VALUES (?, ?)",
            (name, new_pos),
        )
        self.conn.commit()

    def get_top_tasks(self, limit=5):
        # Only get tasks that are not completed, ordered by position
        # Higher position means it's lower in the list if we want it to behave like a stack?
        # Actually, usually "Up" means moving it towards the top of the list (lower index/higher priority).
        # Let's say we order by position DESC so that newest/highest position is at the top.
        self.cursor.execute(
            "SELECT id, name FROM tasks WHERE completed_at IS NULL ORDER BY position DESC LIMIT ?",
            (limit,),
        )
        tasks = self.cursor.fetchall()
        return tasks

    def mark_task_complete(self, task_id):
        self.cursor.execute(
            "UPDATE tasks SET completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (task_id,),
        )
        self.conn.commit()

    def move_task(self, task_id, direction):
        """Move task up or down by swapping positions with the adjacent task."""

        # Get current task position
        self.cursor.execute("SELECT position FROM tasks WHERE id = ?", (task_id,))
        current_pos = self.cursor.fetchone()[0]

        if direction == "up":
            # Moving "up" means finding the task with the smallest position that is greater than current_pos
            # because we are ordering by position DESC
            self.cursor.execute("""
                SELECT id, position FROM tasks 
                WHERE completed_at IS NULL AND position > ? 
                ORDER BY position LIMIT 1
            """, (current_pos,))
        else:
            # Moving "down" means finding the task with the largest position that is smaller than current_pos
            self.cursor.execute("""
                SELECT id, position FROM tasks 
                WHERE completed_at IS NULL AND position < ? 
                ORDER BY position DESC LIMIT 1
            """, (current_pos,))

        other_task = self.cursor.fetchone()
        if other_task:
            other_id, other_pos = other_task
            # Swap positions
            self.cursor.execute("UPDATE tasks SET position = ? WHERE id = ?", (other_pos, task_id))
            self.cursor.execute("UPDATE tasks SET position = ? WHERE id = ?", (current_pos, other_id))
            self.conn.commit()


class TaskFrame(ttk.Frame):
    def __init__(self, parent, on_complete, on_move):
        super().__init__(parent)
        self.on_complete = on_complete
        self.on_move = on_move
        self.columnconfigure(0, weight=1)
        self.labels = []

    def refresh(self, tasks):
        for widget in self.winfo_children():
            widget.destroy()
        self.labels = []

        for i, (task_id, name) in enumerate(tasks):
            lbl = Label(self, text=name, relief="flat", borderwidth=1, anchor="w", takefocus=1)
            lbl.configure(font=font.nametofont("TkDefaultFont"))
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.labels.append(lbl)

            done_btn = ttk.Button(
                self,
                text="✔",
                command=lambda tid=task_id: self.on_complete(tid)
            )
            done_btn.grid(row=i, column=1, padx=2, pady=2)

            # Move Up button
            up_btn = ttk.Button(
                self,
                text="↑",
                width=3,
                command=lambda tid=task_id: self.on_move(tid, "up")
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
    def __init__(self, root, database: Database):
        self.root = root
        self.database = database

        self.root.title("Task Stack")
        
        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(pady=5)
        
        self.new_task_description = ttk.Entry(self.input_frame, width=30)
        self.new_task_description.pack(side=LEFT, padx=5)
        self.new_task_description.bind("<Return>", lambda event: self.handle_new_task())
        
        self.new_task_button = ttk.Button(self.input_frame, text="New task", command=self.handle_new_task)
        self.new_task_button.pack(side=LEFT, padx=5)
        
        self.tasks_frame = TaskFrame(root, self.complete_task, self.move_task)
        self.tasks_frame.pack(pady=5, padx=10, fill=X)
        
        self.selection_index = -1
        self.root.bind_all("<Control-t>", self.focus_new_task)
        self.root.bind_all("<Up>", self.navigate_up)
        self.root.bind_all("<Down>", self.navigate_down)
        
        self.refresh_list()

    def handle_new_task(self):
        name = self.new_task_description.get()
        if name.strip():
            self.database.add_task(name)
            self.new_task_description.delete(0, END)
            self.refresh_list()
        else:
            showwarning("Warning", "Task cannot be empty!")

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

    def refresh_list(self):
        tasks = self.database.get_top_tasks(5)
        self.tasks_frame.refresh(tasks)
        self.selection_index = -1
        self.update_selection()

    def complete_task(self, task_id):
        self.database.mark_task_complete(task_id)
        self.refresh_list()

    def move_task(self, task_id, direction):
        self.database.move_task(task_id, direction)
        self.refresh_list()

def main():

    with Database("tasks.db") as db:
        db.setup()

        root = Tk()
        TaskStackApp(root, db)
        root.mainloop()

if __name__ == "__main__":
    main()

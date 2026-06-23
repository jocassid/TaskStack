#!/usr/bin/env python3

from tkinter import Tk, LEFT, X, END, messagebox, ttk, font, Label
from tkinter.messagebox import showwarning
import sqlite3

def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_task(name):
    if not name.strip():
        return
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_top_tasks(limit=5):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    # Only get tasks that are not completed
    cursor.execute("SELECT id, name FROM tasks WHERE completed_at IS NULL ORDER BY id DESC LIMIT ?", (limit,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def mark_task_complete(task_id):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET completed_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


class TaskFrame(ttk.Frame):
    def __init__(self, parent, on_complete):
        super().__init__(parent)
        self.on_complete = on_complete
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

            btn = ttk.Button(
                self, 
                text="Done",
                command=lambda tid=task_id: self.on_complete(tid)
            )
            btn.grid(row=i, column=1, padx=5, pady=2)


class TaskStackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Stack")
        
        self.input_frame = ttk.Frame(root)
        self.input_frame.pack(pady=5)
        
        self.new_task_description = ttk.Entry(self.input_frame, width=30)
        self.new_task_description.pack(side=LEFT, padx=5)
        self.new_task_description.bind("<Return>", lambda event: self.handle_new_task())
        
        self.new_task_button = ttk.Button(self.input_frame, text="New task", command=self.handle_new_task)
        self.new_task_button.pack(side=LEFT, padx=5)
        
        self.tasks_frame = TaskFrame(root, self.complete_task)
        self.tasks_frame.pack(pady=5, padx=10, fill=X)
        
        self.selection_index = -1
        self.root.bind_all("<Control-t>", self.focus_new_task)
        self.root.bind_all("<Up>", self.navigate_up)
        self.root.bind_all("<Down>", self.navigate_down)
        
        self.refresh_list()

    def handle_new_task(self):
        name = self.new_task_description.get()
        if name.strip():
            add_task(name)
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
        tasks = get_top_tasks(5)
        self.tasks_frame.refresh(tasks)
        self.selection_index = -1
        self.update_selection()

    def complete_task(self, task_id):
        mark_task_complete(task_id)
        self.refresh_list()

def main():
    init_db()
    root = Tk()
    TaskStackApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

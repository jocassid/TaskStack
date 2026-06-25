
from sqlite3 import OperationalError

def add_task_position(conn, cursor):
    # Add the position column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN position INTEGER")
    except OperationalError:
        pass  # Column already exists

    # Initialize position for existing tasks if they have NULL position
    cursor.execute("SELECT id FROM tasks WHERE position IS NULL ORDER BY id")
    rows = cursor.fetchall()
    for row in rows:
        cursor.execute(
            "UPDATE tasks SET position = ? WHERE id = ?",
            (row[0] * 10, row[0]),
        )




ALL_MIGRATIONS = [
    add_task_position,
]
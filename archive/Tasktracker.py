import tkinter as tk
from tkinter import ttk, font
import datetime

class TaskTrackerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Daily Task Tracker")

        # ====== TOP FRAME FOR DEADLINE INPUT ======
        top_frame = tk.Frame(self.master)
        top_frame.pack(pady=10, fill="x")

        # Deadline label
        tk.Label(top_frame, text="Deadline:", font="bold").grid(row=0, column=0, padx=2, sticky="e")

        # Generate time increments with AM/PM
        increments = self.get_time_increments()

        # Times selection (in increments of 15 minutes, with AM/PM)
        self.times_var = tk.StringVar()
        self.times_box = ttk.Combobox(top_frame, textvariable=self.times_var, width=10, values=increments)
        self.times_box.grid(row=0, column=1, padx=2, sticky="w")

        # Start Button
        self.start_button = tk.Button(top_frame, text="Start Countdown", command=self.start_countdown)
        self.start_button.grid(row=0, column=2, padx=10)

        # Dynamic font for time display
        self.dynamic_font = font.Font(family="Helvetica", size=42, weight="bold")
        self.time_remaining_label = tk.Label(top_frame, text="", font=self.dynamic_font)
        self.time_remaining_label.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Bind the window resize event to adjust font size
        self.master.bind("<Configure>", self.resize_fonts)

        # ====== TASKS FRAME WITH BORDER ======
        tasks_container = tk.Frame(self.master, bd=2, relief="groove")
        tasks_container.pack(pady=10, fill="both", expand=True)

        # Canvas and scrollbar for tasks
        self.canvas = tk.Canvas(tasks_container, borderwidth=0)
        self.scrollbar = tk.Scrollbar(tasks_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0,0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.on_frame_configure)

        # Make the task column expand
        self.inner_frame.grid_columnconfigure(0, weight=1)

        # Create header row inside inner_frame
        header_font = ("Helvetica", 10, "bold")
        tk.Label(self.inner_frame, text="Task", font=header_font, anchor="w", width=30).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Label(self.inner_frame, text="Complete", font=header_font, anchor="w").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Label(self.inner_frame, text="Delete", font=header_font, anchor="w").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Add task section
        add_task_frame = tk.Frame(self.master)
        add_task_frame.pack(pady=10)
        tk.Label(add_task_frame, text="New Task:").grid(row=0, column=0, padx=5)
        self.new_task_entry = tk.Entry(add_task_frame, width=30)
        self.new_task_entry.grid(row=0, column=1, padx=5)
        tk.Button(add_task_frame, text="Add Task", command=self.add_task).grid(row=0, column=2, padx=5)

        self.tasks = []  # List of (row_index, entry, var, delete_btn)
        self.task_count = 0

        self.update_id = None
        self.deadline = None

    def get_time_increments(self):
        now = datetime.datetime.now()
        minute = (now.minute // 15 + 1) * 15
        hour = now.hour
        if minute == 60:
            hour += 1
            minute = 0
        if hour >= 24:
            hour -= 24

        increments = []
        h, m = hour, minute
        for _ in range(48):  # 48 increments of 15 mins = 12 hours
            display_hour_24 = h % 24
            # Determine AM/PM and convert 24-hour to 12-hour
            if display_hour_24 == 0:
                display_hour_12 = 12
                ampm = "AM"
            elif display_hour_24 < 12:
                display_hour_12 = display_hour_24
                ampm = "AM"
            elif display_hour_24 == 12:
                display_hour_12 = 12
                ampm = "PM"
            else:
                display_hour_12 = display_hour_24 - 12
                ampm = "PM"

            increments.append(f"{display_hour_12}:{m:02d} {ampm}")

            m += 15
            if m == 60:
                m = 0
                h += 1
            if h == 24:
                h = 0
        return increments

    def resize_fonts(self, event):
        # Adjust the font size based on the current width of the window
        new_size = int(self.master.winfo_width() / 20)
        if new_size < 50:
            new_size = 50
        self.dynamic_font.configure(size=new_size)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_task(self):
        task_text = self.new_task_entry.get().strip()
        if task_text == "":
            return
        self.new_task_entry.delete(0, tk.END)
        self.task_count += 1
        row_index = self.task_count

        # Normal black text on white background, and let it expand horizontally
        task_entry = tk.Entry(self.inner_frame, bg="white", fg="black")
        task_entry.insert(0, task_text)
        task_entry.grid(row=row_index, column=0, padx=5, pady=2, sticky="ew")

        # Checkbutton to toggle completion
        check_var = tk.BooleanVar()
        check_btn = tk.Checkbutton(self.inner_frame, variable=check_var, command=lambda: self.toggle_task(task_entry, check_var))
        check_btn.grid(row=row_index, column=1, padx=5, pady=2)

        # Delete button
        delete_btn = tk.Button(self.inner_frame, text="X", command=lambda: self.delete_task(row_index))
        delete_btn.grid(row=row_index, column=2, padx=5, pady=2)

        self.tasks.append((row_index, task_entry, check_var, delete_btn))

    def toggle_task(self, entry, var):
        if var.get():
            # Green background when completed
            entry.config(bg="green", fg="white")
        else:
            # White background when not completed
            entry.config(bg="white", fg="black")

    def delete_task(self, row_index):
        for i, (r, e, v, d) in enumerate(self.tasks):
            if r == row_index:
                self.tasks.pop(i)
                e.grid_remove()
                d.grid_remove()
                # Remove the checkbutton at column 1 for this row
                for w in self.inner_frame.grid_slaves(row=row_index, column=1):
                    w.grid_remove()
                break

    def start_countdown(self):
        selected_time = self.times_var.get().strip()
        if not selected_time:
            return
        # selected_time looks like "1:15 PM" or "12:00 AM"
        try:
            time_part, ampm = selected_time.split()
            hh_str, mm_str = time_part.split(":")
            hour = int(hh_str)
            minute = int(mm_str)
            ampm = ampm.upper()

            if ampm == "AM":
                if hour == 12:
                    hour = 0
            else:  # PM
                if hour != 12:
                    hour += 12

            now = datetime.datetime.now()
            deadline = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if deadline < now:
                # If deadline passed, assume next day
                deadline += datetime.timedelta(days=1)
            self.deadline = deadline
            if self.update_id is not None:
                self.master.after_cancel(self.update_id)
            self.update_time_remaining()
        except ValueError:
            pass

    def update_time_remaining(self):
        now = datetime.datetime.now()
        diff = self.deadline - now
        if diff.total_seconds() < 0:
            self.time_remaining_label.config(text="Time's up!")
        else:
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_remaining_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.update_id = self.master.after(1000, self.update_time_remaining)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x600")  # Set the default width and height here
    app = TaskTrackerApp(root)
    root.mainloop()

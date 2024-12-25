import csv
import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# ====== Active tasks ======
tasks = []
deadline = None

# Timestamps to track various countdowns
countdown_start_time = None
last_completion_time = None
spent_time_start_time = None

# ====== Log Storage ======
LOG_FILENAME = "task_log.csv"
task_log = {}  # { "Task name": {"fastest_time": 123}, ... }

def load_log():
    """Load the task_log from CSV if it exists."""
    global task_log
    if os.path.exists(LOG_FILENAME):
        with open(LOG_FILENAME, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    task_name, fastest_str = row
                    task_log[task_name] = {"fastest_time": int(fastest_str)}

def save_log():
    """Save the current task_log to CSV."""
    with open(LOG_FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        for name, data in task_log.items():
            writer.writerow([name, data["fastest_time"]])
            
def update_fastest_time(task_name, lap_seconds):
    """
    Compare lap_seconds to existing fastest_time for task_name in task_log.
    If it's faster, update and save.
    """
    global task_log
    if task_name not in task_log:
        # brand new record
        task_log[task_name] = {"fastest_time": lap_seconds}
        save_log()
    else:
        # if new time is faster, update
        if lap_seconds < task_log[task_name]["fastest_time"]:
            task_log[task_name]["fastest_time"] = lap_seconds
            save_log()

# ====== Utility & Timer Functions ======

def get_time_increments():
    """Generate 15-minute increments for the deadline dropdown."""
    now = datetime.now()
    minute = (now.minute // 15 + 1) * 15
    hour = now.hour
    if minute == 60:
        hour += 1
        minute = 0
    if hour >= 24:
        hour -= 24

    increments = []
    h, m = hour, minute
    for _ in range(48):  # 48 increments => 12 hours
        display_hour_24 = h % 24
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

def format_deadline(d):
    """Return a user-friendly HH:MM AM/PM string for the deadline."""
    if d is None:
        return None
    hour_24 = d.hour
    minute = d.minute
    ampm = "AM"
    if hour_24 == 0:
        display_hour = 12
    elif hour_24 < 12:
        display_hour = hour_24
    elif hour_24 == 12:
        display_hour = 12
        ampm = "PM"
    else:
        display_hour = hour_24 - 12
        ampm = "PM"
    return f"{display_hour}:{minute:02d} {ampm}"

def format_lap_time(seconds):
    """
    Convert an integer number of seconds into e.g. 'Xh Xm Xs' or 'Mm Ss'.
    90 => '1m 30s'; 3700 => '1h 1m 40s'
    """
    if seconds < 60:
        return f"{seconds}s"
    hrs = seconds // 3600
    secs_left = seconds % 3600
    mins = secs_left // 60
    secs = secs_left % 60
    if hrs > 0:
        return f"{hrs}h {mins}m {secs}s"
    else:
        return f"{mins}m {secs}s"


# ====== Routes ======

@app.route('/')
def index():
    increments = get_time_increments()
    all_done = (len(tasks) > 0) and all(t['completed'] for t in tasks)
    deadline_str = format_deadline(deadline)

    # Pass format_lap_time into the template so Jinja can call it
    return render_template(
        'index.html',
        tasks=tasks,
        increments=increments,
        all_done=all_done,
        deadline_str=deadline_str,
        task_log=task_log,
        format_lap_time=format_lap_time
    )


@app.route('/add', methods=['POST'])
def add_task():
    task_text = request.form.get('task_text', '').strip()
    if task_text:
        tasks.append({
            'text': task_text,
            'completed': False,
            'lap_time': None
        })
    return redirect(url_for('index'))


@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    global last_completion_time, spent_time_start_time
    if 0 <= task_id < len(tasks):
        task = tasks[task_id]
        if not task['completed']:
            # Mark as completed
            task['completed'] = True
            now = datetime.now()
            if last_completion_time is not None:
                diff = (now - last_completion_time).total_seconds()
            else:
                diff = 0
            lap_seconds = int(diff)
            task['lap_time'] = format_lap_time(lap_seconds)

            last_completion_time = now
            spent_time_start_time = now

            # Update the log with new possible fastest time
            update_fastest_time(task['text'], lap_seconds)
        else:
            # Unmark as completed
            task['completed'] = False
            task['lap_time'] = None
    return redirect(url_for('index'))


@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 0 <= task_id < len(tasks):
        del tasks[task_id]
    return redirect(url_for('index'))


@app.route('/set_deadline', methods=['POST'])
def set_deadline():
    global deadline, countdown_start_time, last_completion_time, spent_time_start_time
    time_input = request.form.get('deadline', '').strip()
    if time_input:
        try:
            time_part, ampm = time_input.split()
            hh_str, mm_str = time_part.split(':')
            hour = int(hh_str)
            minute = int(mm_str)
            ampm = ampm.upper()

            if ampm == 'AM':
                if hour == 12:
                    hour = 0
            else:  # PM
                if hour != 12:
                    hour += 12

            now = datetime.now()
            deadline_candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if deadline_candidate < now:
                deadline_candidate += timedelta(days=1)
            deadline = deadline_candidate

            countdown_start_time = now
            last_completion_time = now
            spent_time_start_time = now
        except:
            pass
    return redirect(url_for('index'))


@app.route('/reset_deadline', methods=['POST'])
def reset_deadline():
    global deadline, countdown_start_time, last_completion_time, spent_time_start_time
    deadline = None
    countdown_start_time = None
    last_completion_time = None
    spent_time_start_time = None
    return redirect(url_for('index'))


@app.route('/get_remaining_time')
def get_remaining_time():
    if deadline:
        now = datetime.now()
        diff = deadline - now
        seconds_left = max(int(diff.total_seconds()), 0)
        return str(seconds_left)
    return '0'


@app.route('/get_spent_time')
def get_spent_time():
    global spent_time_start_time
    if spent_time_start_time is None:
        return '0'
    now = datetime.now()
    diff = now - spent_time_start_time
    return str(int(diff.total_seconds()))


@app.route('/add_task_from_log/<task_name>')
def add_task_from_log(task_name):
    tasks.append({
        'text': task_name,
        'completed': False,
        'lap_time': None
    })
    return redirect(url_for('index'))

@app.route('/delete_from_log/<task_name>')
def delete_from_log(task_name):
    if task_name in task_log:
        del task_log[task_name]
        save_log()
    return redirect(url_for('index'))



if __name__ == "__main__":
    load_log()  # Ensure we load the CSV before app.run
    app.run(debug=True)

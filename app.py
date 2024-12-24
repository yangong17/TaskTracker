from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

tasks = []
deadline = None

# We'll store these two times so we know when the user "started"
# and can compute the intervals for each completed task
countdown_start_time = None
last_completion_time = None

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
    for _ in range(48):  # 48 increments of 15 mins => 12 hours
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
    """Display a user-friendly string for the stored deadline."""
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
    Convert an integer number of seconds into a quick "Xh Xm Xs" format,
    or "Mm Ss" if under an hour, etc. Adjust to taste.
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

@app.route('/')
def index():
    increments = get_time_increments()
    # Check if all tasks are complete
    all_done = (len(tasks) > 0) and all(t['completed'] for t in tasks)
    deadline_str = format_deadline(deadline)
    return render_template(
        'index.html',
        tasks=tasks,
        increments=increments,
        all_done=all_done,
        deadline_str=deadline_str
    )

@app.route('/add', methods=['POST'])
def add_task():
    task_text = request.form.get('task_text', '').strip()
    if task_text:
        tasks.append({
            'text': task_text,
            'completed': False,
            'lap_time': None  # Will fill when user completes the task
        })
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    global last_completion_time
    if 0 <= task_id < len(tasks):
        task = tasks[task_id]
        # Toggle logic
        if not task['completed']:
            # Mark as completed
            task['completed'] = True
            now = datetime.now()
            # If no last_completion_time set yet, or we haven't started the countdown
            # we can't calculate. But normally, this is set when we do set_deadline.
            if last_completion_time is not None:
                diff = (now - last_completion_time).total_seconds()
            else:
                diff = 0
            task['lap_time'] = format_lap_time(int(diff))
            # Update the last completion time
            last_completion_time = now
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
    """
    When setting a deadline, we also record the 'start' time.
    The first completed task is measured vs. this start time,
    and subsequent tasks are measured vs. the last completion time.
    """
    global deadline, countdown_start_time, last_completion_time
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

            # Record the start times
            countdown_start_time = datetime.now()
            last_completion_time = countdown_start_time
        except:
            pass
    return redirect(url_for('index'))

@app.route('/reset_deadline', methods=['POST'])
def reset_deadline():
    global deadline, countdown_start_time, last_completion_time
    # Clear everything
    deadline = None
    countdown_start_time = None
    last_completion_time = None
    return redirect(url_for('index'))

@app.route('/get_remaining_time')
def get_remaining_time():
    if deadline:
        now = datetime.now()
        diff = deadline - now
        seconds_left = max(int(diff.total_seconds()), 0)
        return str(seconds_left)
    return '0'

if __name__ == "__main__":
    app.run(debug=True)

import csv
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# ====== Active tasks ======
tasks = []
deadline = None

# Focus Mode / Pomodoro Timer state
focus_mode = False
pomodoro_work_minutes = 25
pomodoro_rest_minutes = 5
pomodoro_is_work_session = True
pomodoro_start_time = None
pomodoro_is_running = False
pomodoro_paused_elapsed = 0  # Track elapsed time when paused

# Session counters
work_sessions_completed = 0
rest_sessions_completed = 0

# Timestamps to track various countdowns
countdown_start_time = None
last_completion_time = None
spent_time_start_time = None

# ====== Storage ======
LOG_FILENAME = "task_log.csv"
FAVORITES_FILENAME = "favorites.csv"
task_log = {}  # { "Task name": {"fastest_time": 123}, ... }
favorites = []  # List of favorite task names

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
        task_log = dict(sorted(task_log.items()))  # Sort alphabetically by keys
    else:
        # If no log file exists, populate with sample data
        populate_sample_log()

def populate_sample_log():
    """Populate the task log with comprehensive sample data for demonstration."""
    global task_log
    sample_tasks = {
        # Work & Productivity
        "Check emails": 300,  # 5 minutes
        "Daily standup meeting": 900,  # 15 minutes
        "Code review": 1800,  # 30 minutes
        "Write documentation": 2700,  # 45 minutes
        "Update project status": 600,  # 10 minutes
        "Respond to client feedback": 1200,  # 20 minutes
        "Plan weekly tasks": 1500,  # 25 minutes
        "Research new tools": 3600,  # 1 hour
        "Team brainstorming session": 2400,  # 40 minutes
        "Prepare presentation": 4800,  # 1 hour 20 minutes
        
        # Personal Development
        "Read industry articles": 1800,  # 30 minutes
        "Online course lesson": 2700,  # 45 minutes
        "Practice coding problem": 1200,  # 20 minutes
        "Watch tutorial video": 900,  # 15 minutes
        "Update LinkedIn profile": 600,  # 10 minutes
        "Network with colleagues": 1800,  # 30 minutes
        "Review course notes": 900,  # 15 minutes
        "Complete certification exam": 7200,  # 2 hours
        
        # Health & Wellness
        "Morning workout": 1800,  # 30 minutes
        "Meditation session": 600,  # 10 minutes
        "Prepare healthy lunch": 900,  # 15 minutes
        "Evening walk": 1200,  # 20 minutes
        "Yoga practice": 2400,  # 40 minutes
        "Drink water reminder": 60,  # 1 minute
        "Stretch break": 300,  # 5 minutes
        "Plan workout routine": 600,  # 10 minutes
        
        # Household & Personal
        "Tidy kitchen": 600,  # 10 minutes
        "Do laundry": 300,  # 5 minutes (active time)
        "Vacuum living room": 900,  # 15 minutes
        "Pay monthly bills": 1200,  # 20 minutes
        "Grocery shopping": 2700,  # 45 minutes
        "Clean bathroom": 1800,  # 30 minutes
        "Organize desk": 900,  # 15 minutes
        "Water plants": 300,  # 5 minutes
        "Take out trash": 180,  # 3 minutes
        "Meal prep": 3600,  # 1 hour
        
        # Creative & Hobbies
        "Write journal entry": 900,  # 15 minutes
        "Practice guitar": 1800,  # 30 minutes
        "Draw or sketch": 2400,  # 40 minutes
        "Photo editing": 1800,  # 30 minutes
        "Blog post writing": 3600,  # 1 hour
        "Learn new song": 2700,  # 45 minutes
        "Craft project": 4800,  # 1 hour 20 minutes
        
        # Social & Communication
        "Call family member": 1200,  # 20 minutes
        "Video chat with friends": 2400,  # 40 minutes
        "Plan social event": 1800,  # 30 minutes
        "Send thank you notes": 600,  # 10 minutes
        "Social media update": 300,  # 5 minutes
        
        # Learning & Study
        "Review flashcards": 900,  # 15 minutes
        "Complete homework": 2700,  # 45 minutes
        "Research assignment": 3600,  # 1 hour
        "Study for exam": 5400,  # 1.5 hours
        "Language practice": 1800,  # 30 minutes
        "Take online quiz": 600,  # 10 minutes
        
        # Finance & Planning
        "Budget review": 1800,  # 30 minutes
        "Investment research": 2700,  # 45 minutes
        "Plan vacation": 3600,  # 1 hour
        "File taxes": 7200,  # 2 hours
        "Review insurance": 1200,  # 20 minutes
        "Update resume": 2400,  # 40 minutes
        
        # Technology & Maintenance
        "Backup computer files": 900,  # 15 minutes
        "Update software": 600,  # 10 minutes
        "Clean desktop files": 1200,  # 20 minutes
        "Password manager update": 600,  # 10 minutes
        "Phone storage cleanup": 900,  # 15 minutes
        "Install app updates": 300,  # 5 minutes
        
        # Quick Tasks
        "Make bed": 120,  # 2 minutes
        "Check weather": 60,  # 1 minute
        "Set daily alarm": 120,  # 2 minutes
        "Quick room scan": 180,  # 3 minutes
        "Lock doors": 60,  # 1 minute
        "Turn off lights": 60,  # 1 minute
        
        # Your existing tasks (preserved)
        "Sort vlogs": 3328,
        "Stats dashboard": 5,
        "test": 0,
        "tes 2": 1,
        "test 3": 3,
        "test 2": 17
    }
    
    task_log = sample_tasks
    save_log()  # Save the sample data to CSV

def save_log():
    """Save the current task_log to CSV."""
    with open(LOG_FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        for name, data in task_log.items():
            writer.writerow([name, data["fastest_time"]])

def load_favorites():
    """Load the favorites list from CSV if it exists. If not, create an empty file."""
    global favorites
    if os.path.exists(FAVORITES_FILENAME):
        with open(FAVORITES_FILENAME, 'r', newline='') as f:
            reader = csv.reader(f)
            favorites = [row[0] for row in reader if row]
    else:
        favorites = []
        # Create an empty favorites.csv file
        with open(FAVORITES_FILENAME, 'w', newline='') as f:
            pass

def save_favorites():
    """Save the current favorites list to CSV."""
    with open(FAVORITES_FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        for fav in favorites:
            writer.writerow([fav])
            
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

def sort_tasks_by_priority():
    """Sort tasks by priority (1=highest, higher numbers=lower priority), then by creation order."""
    global tasks
    tasks.sort(key=lambda t: (t.get('priority', 5), t.get('created_at', datetime.now())))

def sort_tasks_by_priority_desc():
    """Sort tasks by priority descending (highest number first), then by creation order."""
    global tasks
    tasks.sort(key=lambda t: (-t.get('priority', 5), t.get('created_at', datetime.now())))

def sort_tasks_by_deadline():
    """Sort tasks by deadline (earliest first), then by priority, then by creation order."""
    global tasks
    def deadline_sort_key(task):
        deadline = task.get('task_deadline')
        if deadline is None:
            # Tasks without deadlines go to the end
            return (datetime.max, task.get('priority', 5), task.get('created_at', datetime.now()))
        return (deadline, task.get('priority', 5), task.get('created_at', datetime.now()))
    
    tasks.sort(key=deadline_sort_key)

def get_current_working_task():
    """Get the highest priority incomplete task (lowest number = highest priority)."""
    incomplete_tasks = [task for task in tasks if not task.get('completed', False)]
    if not incomplete_tasks:
        return None
    
    # Sort by priority (lowest number first), then by creation time
    incomplete_tasks.sort(key=lambda t: (t.get('priority', 5), t.get('created_at', datetime.now())))
    return incomplete_tasks[0]

def is_task_overdue(task):
    """Check if a task is overdue based on its deadline."""
    if not task.get('task_deadline'):
        return False
    return datetime.now() > task['task_deadline']

def get_priority_color(priority_value):
    """Get the color for a priority value - lower numbers = higher priority = redder colors."""
    if priority_value == 1:
        return '#dc3545'  # Red - highest priority
    elif priority_value == 2:
        return '#fd7e14'  # Orange
    elif priority_value == 3:
        return '#ffc107'  # Yellow
    elif priority_value == 4:
        return '#20c997'  # Teal
    elif priority_value == 5:
        return '#28a745'  # Green - lowest priority
    else:
        return '#6c757d'  # Gray for any other values

# ====== Utility & Timer Functions ======

def get_time_increments():
    """Generate 15-minute increments for the deadline dropdown."""
    now = datetime.now()
    minute = (now.minute // 15 + 1) * 15
    hour = now.hour
    
    # Handle minute and hour overflow
    if minute >= 60:
        hour += 1
        minute = 0
    if hour >= 24:
        hour = 0  # Use 0 instead of subtracting 24 for clarity

    increments = []
    h, m = hour, minute
    for _ in range(48):  # 48 increments => 12 hours
        display_hour_24 = h % 24  # Ensure we stay in 0-23 range
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
        if m >= 60:  # Use >= for consistency
            m = 0
            h += 1
        if h >= 24:  # Use >= for consistency
            h = 0
    return increments

def get_task_deadline_increments():
    """Generate 15-minute increments for task deadlines (next 12 hours, matching countdown deadline)."""
    now = datetime.now()
    increments = []
    
    # Start from next 15-minute increment
    minute = (now.minute // 15 + 1) * 15
    hour = now.hour
    
    # Handle minute overflow and hour boundary
    if minute >= 60:
        hour += 1
        minute = 0
    
    # Handle hour overflow (24-hour boundary)
    if hour >= 24:
        hour = 0
        # We need to add a day when hour wraps around
        now = now + timedelta(days=1)
    
    try:
        start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError as e:
        # Fallback: use current time + 15 minutes
        start_time = now + timedelta(minutes=15)
        start_time = start_time.replace(second=0, microsecond=0)
    
    # Ensure start_time is in the future
    if start_time <= now:
        start_time += timedelta(minutes=15)
    
    for i in range(48):  # 48 * 15 minutes = 12 hours (matching countdown deadline)
        time_option = start_time + timedelta(minutes=i * 15)
        display_hour_24 = time_option.hour
        
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
        
        # Just show the time without day prefix
        display_text = f"{display_hour_12}:{time_option.minute:02d} {ampm}"
        increments.append({
            'value': time_option.isoformat(),
            'text': display_text
        })
    
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

def format_task_deadline(task_deadline):
    """Format task deadline for display."""
    if not task_deadline:
        return ""
    
    now = datetime.now()
    
    # Check if it's today or tomorrow
    if task_deadline.date() == now.date():
        day_part = "Today"
    elif task_deadline.date() == (now + timedelta(days=1)).date():
        day_part = "Tomorrow"
    else:
        day_part = task_deadline.strftime("%m/%d")
    
    hour_24 = task_deadline.hour
    if hour_24 == 0:
        display_hour = 12
        ampm = "AM"
    elif hour_24 < 12:
        display_hour = hour_24
        ampm = "AM"
    elif hour_24 == 12:
        display_hour = 12
        ampm = "PM"
    else:
        display_hour = hour_24 - 12
        ampm = "PM"
    
    return f"{day_part} {display_hour}:{task_deadline.minute:02d} {ampm}"

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
    task_deadline_increments = get_task_deadline_increments()
    all_done = (len(tasks) > 0) and all(t['completed'] for t in tasks)
    deadline_str = format_deadline(deadline)
    current_working_task = get_current_working_task()

    # Sort tasks by priority before displaying (default: lowest number = highest priority)
    sort_tasks_by_priority()

    # Pass format_lap_time into the template so Jinja can call it
    return render_template(
        'index.html',
        tasks=tasks,
        increments=increments,
        task_deadline_increments=task_deadline_increments,
        all_done=all_done,
        deadline_str=deadline_str,
        task_log=task_log,
        favorites=favorites,
        current_working_task=current_working_task,
        focus_mode=focus_mode,
        pomodoro_work_minutes=pomodoro_work_minutes,
        pomodoro_rest_minutes=pomodoro_rest_minutes,
        pomodoro_is_work_session=pomodoro_is_work_session,
        pomodoro_is_running=pomodoro_is_running,
        pomodoro_is_paused=(pomodoro_start_time is not None and not pomodoro_is_running),
        work_sessions_completed=work_sessions_completed,
        rest_sessions_completed=rest_sessions_completed,
        format_lap_time=format_lap_time,
        format_task_deadline=format_task_deadline,
        get_priority_color=get_priority_color,
        is_task_overdue=is_task_overdue
    )

# ====== AJAX-Enhanced Routes ======

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks as JSON for AJAX updates."""
    current_working_task = get_current_working_task()
    all_done = (len(tasks) > 0) and all(t['completed'] for t in tasks)
    
    return jsonify({
        'tasks': tasks,
        'current_working_task': current_working_task.get('text', '') if current_working_task else '',
        'all_done': all_done,
        'task_deadline_increments': get_task_deadline_increments()
    })

# Clear tasks
@app.route('/clear_tasks', methods=['POST'])
def clear_tasks():
    global tasks
    
    tasks.clear()  # Empties the tasks list
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'All tasks cleared'
        })
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_task():
    task_text = request.form.get('task_text', '').strip()
    if task_text:
        new_task = {
            'text': task_text,
            'completed': False,
            'lap_time': None,
            'priority': 3,  # Default to middle priority
            'task_deadline': None,
            'created_at': datetime.now()
        }
        tasks.append(new_task)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'task': new_task,
                'task_index': len(tasks) - 1
            })
    return redirect(url_for('index'))

@app.route('/update_priority/<int:task_id>', methods=['POST'])
def update_priority(task_id):
    response_data = {'success': False}
    
    if 0 <= task_id < len(tasks):
        priority = int(request.form.get('priority', 3))
        tasks[task_id]['priority'] = priority
        response_data = {
            'success': True,
            'task_id': task_id,
            'priority': priority
        }
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/update_task_deadline/<int:task_id>', methods=['POST'])
def update_task_deadline(task_id):
    response_data = {'success': False}
    
    if 0 <= task_id < len(tasks):
        deadline_str = request.form.get('task_deadline', '').strip()
        if deadline_str:
            try:
                task_deadline = datetime.fromisoformat(deadline_str)
                tasks[task_id]['task_deadline'] = task_deadline
                response_data = {
                    'success': True,
                    'task_id': task_id,
                    'deadline': task_deadline.isoformat(),
                    'deadline_display': format_task_deadline(task_deadline)
                }
            except:
                response_data = {'success': False, 'error': 'Invalid datetime format'}
        else:
            tasks[task_id]['task_deadline'] = None
            response_data = {
                'success': True,
                'task_id': task_id,
                'deadline': None
            }
            
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/sort_priority_asc', methods=['POST'])
def sort_priority_asc():
    """Sort tasks by priority ascending (1, 2, 3, 4, 5)"""
    sort_tasks_by_priority()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'tasks': tasks,
            'sort_type': 'priority_asc'
        })
    return redirect(url_for('index'))

@app.route('/sort_priority_desc', methods=['POST'])
def sort_priority_desc():
    """Sort tasks by priority descending (5, 4, 3, 2, 1)"""
    sort_tasks_by_priority_desc()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'tasks': tasks,
            'sort_type': 'priority_desc'
        })
    return redirect(url_for('index'))

@app.route('/sort_deadline_asc', methods=['POST'])
def sort_deadline_asc():
    """Sort tasks by deadline ascending (earliest first)"""
    sort_tasks_by_deadline()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'tasks': tasks,
            'sort_type': 'deadline_asc'
        })
    return redirect(url_for('index'))

@app.route('/sort_deadline_desc', methods=['POST'])
def sort_deadline_desc():
    """Sort tasks by deadline descending (latest first)"""
    sort_tasks_by_deadline()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    global last_completion_time, spent_time_start_time
    response_data = {'success': False}
    
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
            
            response_data = {
                'success': True,
                'task': task,
                'task_id': task_id,
                'lap_time': task['lap_time']
            }
        else:
            # Unmark as completed
            task['completed'] = False
            task['lap_time'] = None
            response_data = {
                'success': True,
                'task': task,
                'task_id': task_id
            }
            
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    response_data = {'success': False}
    
    if 0 <= task_id < len(tasks):
        del tasks[task_id]
        response_data = {
            'success': True,
            'task_id': task_id,
            'remaining_tasks': len(tasks)
        }
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/set_deadline', methods=['POST'])
def set_deadline():
    global deadline, countdown_start_time, last_completion_time, spent_time_start_time
    
    time_input = request.form.get('deadline', '').strip()
    response_data = {'success': False}
    
    if time_input:
        try:
            time_part, ampm = time_input.split()
            hh_str, mm_str = time_part.split(':')
            hour = int(hh_str)
            minute = int(mm_str)
            ampm = ampm.upper()

            # Validate input ranges
            if not (1 <= hour <= 12):
                raise ValueError("Hour must be between 1 and 12")
            if not (0 <= minute <= 59):
                raise ValueError("Minute must be between 0 and 59")

            # Convert to 24-hour format
            if ampm == 'AM':
                if hour == 12:
                    hour = 0  # 12 AM = 00:xx
            elif ampm == 'PM':
                if hour != 12:
                    hour += 12  # 1 PM = 13:xx, 11 PM = 23:xx
                # 12 PM stays as 12 (12:xx)
            else:
                raise ValueError("AM/PM indicator must be AM or PM")

            # Final validation for 24-hour format
            if not (0 <= hour <= 23):
                raise ValueError(f"Converted hour {hour} is out of range")

            now = datetime.now()
            deadline_candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if deadline_candidate < now:
                deadline_candidate += timedelta(days=1)
            deadline = deadline_candidate

            countdown_start_time = now
            last_completion_time = now
            spent_time_start_time = now
            
            response_data = {
                'success': True,
                'deadline': deadline.isoformat(),
                'deadline_display': format_deadline(deadline)
            }
            
        except ValueError as e:
            response_data = {'success': False, 'error': f'Invalid time format: {str(e)}'}
        except Exception as e:
            response_data = {'success': False, 'error': f'Invalid time format: {str(e)}'}
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/reset_deadline', methods=['POST'])
def reset_deadline():
    global deadline, countdown_start_time, last_completion_time, spent_time_start_time
    deadline = None
    countdown_start_time = None
    last_completion_time = None
    spent_time_start_time = None
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Timer reset'
        })
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
    new_task = {
        'text': task_name,
        'completed': False,
        'lap_time': None,
        'priority': 3,  # Default to middle priority
        'task_deadline': None,
        'created_at': datetime.now()
    }
    tasks.append(new_task)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'task': new_task,
            'task_index': len(tasks) - 1
        })
    return redirect(url_for('index'))

@app.route('/delete_from_log/<task_name>')
def delete_from_log(task_name):
    response_data = {'success': False}
    
    if task_name in task_log:
        del task_log[task_name]
        save_log()
        response_data = {
            'success': True,
            'deleted_task': task_name,
            'task_log': task_log
        }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

# ====== Favorites Routes (AJAX Enhanced) ======

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    fav_text = request.form.get('favorite_text', '').strip()
    response_data = {'success': False}
    
    if fav_text and fav_text not in favorites:
        favorites.append(fav_text)
        save_favorites()
        response_data = {
            'success': True,
            'favorite': fav_text,
            'favorites': favorites
        }
    elif fav_text in favorites:
        response_data = {'success': False, 'error': 'Favorite already exists'}
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

@app.route('/add_task_from_favorite/<favorite_name>')
def add_task_from_favorite(favorite_name):
    new_task = {
        'text': favorite_name,
        'completed': False,
        'lap_time': None,
        'priority': 3,  # Default to middle priority
        'task_deadline': None,
        'created_at': datetime.now()
    }
    tasks.append(new_task)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'task': new_task,
            'task_index': len(tasks) - 1
        })
    return redirect(url_for('index'))

@app.route('/delete_favorite/<favorite_name>')
def delete_favorite(favorite_name):
    response_data = {'success': False}
    
    if favorite_name in favorites:
        favorites.remove(favorite_name)
        save_favorites()
        response_data = {
            'success': True,
            'deleted_favorite': favorite_name,
            'favorites': favorites
        }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(response_data)
    return redirect(url_for('index'))

# ====== Focus Mode Routes ======

@app.route('/toggle_focus_mode', methods=['POST'])
def toggle_focus_mode():
    global focus_mode, pomodoro_start_time, pomodoro_is_running
    global work_sessions_completed, rest_sessions_completed
    focus_mode = not focus_mode
    
    # Reset pomodoro timer when exiting focus mode
    if not focus_mode:
        pomodoro_start_time = None
        pomodoro_is_running = False
        work_sessions_completed = 0
        rest_sessions_completed = 0
    
    return redirect(url_for('index'))

@app.route('/update_pomodoro_settings', methods=['POST'])
def update_pomodoro_settings():
    global pomodoro_work_minutes, pomodoro_rest_minutes
    
    work_mins = request.form.get('work_minutes')
    rest_mins = request.form.get('rest_minutes')
    
    if work_mins and work_mins.isdigit():
        pomodoro_work_minutes = int(work_mins)
    if rest_mins and rest_mins.isdigit():
        pomodoro_rest_minutes = int(rest_mins)
    
    return redirect(url_for('index'))

@app.route('/start_pomodoro', methods=['POST'])
def start_pomodoro():
    global pomodoro_start_time, pomodoro_is_running, pomodoro_paused_elapsed
    pomodoro_start_time = datetime.now()
    pomodoro_is_running = True
    pomodoro_paused_elapsed = 0  # Reset paused time when starting fresh
    return redirect(url_for('index'))

@app.route('/pause_pomodoro', methods=['POST'])
def pause_pomodoro():
    global pomodoro_is_running, pomodoro_paused_elapsed
    pomodoro_is_running = False
    now = datetime.now()
    if pomodoro_start_time:
        pomodoro_paused_elapsed = (now - pomodoro_start_time).total_seconds()
    return redirect(url_for('index'))

@app.route('/resume_pomodoro', methods=['POST'])
def resume_pomodoro():
    global pomodoro_start_time, pomodoro_is_running, pomodoro_paused_elapsed
    pomodoro_start_time = datetime.now() - timedelta(seconds=pomodoro_paused_elapsed)
    pomodoro_is_running = True
    pomodoro_paused_elapsed = 0 # Reset paused elapsed time
    return redirect(url_for('index'))

@app.route('/reset_pomodoro', methods=['POST'])
def reset_pomodoro():
    global pomodoro_start_time, pomodoro_is_running, pomodoro_is_work_session, pomodoro_paused_elapsed
    global work_sessions_completed, rest_sessions_completed
    pomodoro_start_time = None
    pomodoro_is_running = False
    pomodoro_is_work_session = True
    pomodoro_paused_elapsed = 0
    work_sessions_completed = 0
    rest_sessions_completed = 0
    return redirect(url_for('index'))

@app.route('/get_pomodoro_time')
def get_pomodoro_time():
    """Get remaining time in current pomodoro session"""
    global pomodoro_is_work_session, pomodoro_start_time, pomodoro_is_running, pomodoro_paused_elapsed
    global work_sessions_completed, rest_sessions_completed
    
    # Calculate session duration for current session type
    session_duration = pomodoro_work_minutes * 60 if pomodoro_is_work_session else pomodoro_rest_minutes * 60
    
    if not pomodoro_start_time:
        # Timer hasn't been started yet, return full duration
        return jsonify({
            'remaining_seconds': session_duration,
            'is_work_session': pomodoro_is_work_session,
            'is_running': False,
            'session_complete': False,
            'session_changed': False,
            'work_sessions_completed': work_sessions_completed,
            'rest_sessions_completed': rest_sessions_completed
        })
    
    now = datetime.now()
    
    # Calculate elapsed time
    if pomodoro_is_running:
        elapsed_seconds = (now - pomodoro_start_time).total_seconds()
    else:
        # When paused, use the stored elapsed time
        elapsed_seconds = pomodoro_paused_elapsed
    
    remaining_seconds = max(0, session_duration - elapsed_seconds)
    
    session_complete = remaining_seconds <= 0
    session_changed = False
    
    # Handle automatic session transition
    if session_complete and pomodoro_is_running:
        # Increment the completed session counter
        if pomodoro_is_work_session:
            work_sessions_completed += 1
        else:
            rest_sessions_completed += 1
            
        # Switch to the next session type
        pomodoro_is_work_session = not pomodoro_is_work_session
        session_changed = True
        
        # Automatically start the new session (continuous cycling)
        pomodoro_start_time = now
        pomodoro_is_running = True
        pomodoro_paused_elapsed = 0
        
        # Calculate the duration for the NEW session type
        new_session_duration = pomodoro_work_minutes * 60 if pomodoro_is_work_session else pomodoro_rest_minutes * 60
        
        # Return the new session info with full duration
        return jsonify({
            'remaining_seconds': new_session_duration,
            'is_work_session': pomodoro_is_work_session,
            'is_running': True,  # Keep running for continuous cycling
            'session_complete': True,
            'session_changed': True,
            'previous_session_was_work': not pomodoro_is_work_session,
            'work_sessions_completed': work_sessions_completed,
            'rest_sessions_completed': rest_sessions_completed
        })
    
    return jsonify({
        'remaining_seconds': int(remaining_seconds),
        'is_work_session': pomodoro_is_work_session,
        'is_running': pomodoro_is_running,
        'session_complete': session_complete,
        'session_changed': session_changed,
        'work_sessions_completed': work_sessions_completed,
        'rest_sessions_completed': rest_sessions_completed
    })

if __name__ == "__main__":
    load_log()  # Ensure we load the CSV before app.run
    load_favorites()  # Load favorites
    app.run(debug=True)

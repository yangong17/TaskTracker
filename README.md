# Task Tracker with Timer

A Flask-based task management application that helps you track tasks, manage deadlines, and stay focused with built-in timers and study ambiance.

## Features

- **Task Management**
  - Add, edit, and delete tasks
  - Set priority levels (1-5)
  - Assign individual task deadlines
  - Mark tasks as complete
  - Track completion times

- **Time Management**
  - Set overall session deadline
  - Countdown timer
  - Time tracking for each task
  - Visual alerts for approaching deadlines

- **Focus Tools**
  - Focus Mode with Pomodoro Timer
  - Study ambiance with lofi music
  - Work/rest session tracking
  - Visual session progress

- **Task History**
  - Track fastest completion times
  - Save favorite tasks for quick access
  - Task completion log

## Getting Started

### Prerequisites
- Python 3.x
- Flask

### Installation
1. Clone the repository
2. Install dependencies:
   ```
   pip install flask
   ```
3. Run the application:
   ```
   python app.py
   ```

## How to Use

### Basic Task Management

1. **Input Your Tasks**
   - Enter task name in the "New task" field
   - Set priority (1 = highest, 5 = lowest)
   - Assign a deadline if needed
   - Tasks are automatically sorted by priority

2. **Set Overall Deadline**
   - Choose a deadline from the dropdown
   - Click "Start Countdown" to begin the timer
   - The main timer will show remaining time

3. **Start Working**
   - The timer will begin counting down
   - Time spent on current task is tracked
   - Visual alerts appear when deadlines approach

4. **Complete Tasks**
   - Click "Complete" when a task is finished
   - Task completion times are recorded
   - Completed tasks turn green

5. **Study Ambiance**
   - Click "Show Video" to display lofi music player
   - Perfect background music for studying
   - Toggle video visibility as needed

### Advanced Features

#### Focus Mode
- Toggle Focus Mode for distraction-free work
- Built-in Pomodoro Timer
  - Customizable work/rest intervals
  - Session tracking
  - Visual progress indicators

#### Task Organization
- Sort tasks by:
  - Priority (ascending/descending)
  - Deadline
- Save frequently used tasks as favorites
- Track personal best times for recurring tasks

#### Visual Indicators
- Color-coded priorities
- Deadline warnings
- Task completion status
- Session progress
- Dark/Light mode toggle

## Tips for Best Use

1. **Priority Management**
   - Use priority 1 for urgent tasks
   - Balance tasks across priority levels
   - Regularly review and adjust priorities

2. **Time Management**
   - Set realistic deadlines
   - Use the Pomodoro timer for focused work
   - Take regular breaks during long sessions

3. **Task History**
   - Review completion times to improve estimates
   - Save common tasks as favorites
   - Use the log to track productivity patterns

## Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT). 
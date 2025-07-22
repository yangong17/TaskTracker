document.addEventListener('DOMContentLoaded', () => {
    const countdownEl = document.getElementById('countdown');
    const spentTimeEl = document.getElementById('spent-time');

    // Check if we're in focus mode
    if (focusMode) {
        initFocusMode();
        return;
    }

    // If all tasks complete, show "All tasks complete" and do not update timers
    if (allDone) {
        countdownEl.innerText = "All tasks complete";
        countdownEl.style.color = "green";
        spentTimeEl.innerText = "0:00";
        launchConfetti();
        return;
    }

    setInterval(updateAllTimers, 1000);
    updateAllTimers();

    // Initialize priority select styling
    initializePrioritySelects();

    function initFocusMode() {
        const pomodoroTimerEl = document.getElementById('pomodoro-timer');
        const sessionTypeEl = document.getElementById('session-type');
        
        if (!pomodoroTimerEl || !sessionTypeEl) return;

        // Update pomodoro timer every second
        setInterval(updatePomodoroTimer, 1000);
        updatePomodoroTimer();
    }

    function updatePomodoroTimer() {
        const pomodoroTimerEl = document.getElementById('pomodoro-timer');
        const sessionTypeEl = document.getElementById('session-type');
        const progressCircle = document.getElementById('progress-circle');
        
        if (!pomodoroTimerEl || !sessionTypeEl || !progressCircle) return;

        fetch('/get_pomodoro_time')
            .then(r => r.json())
            .then(data => {
                const { remaining_seconds, is_work_session, is_running, session_complete, session_changed, previous_session_was_work, work_sessions_completed, rest_sessions_completed } = data;
                
                // Update session counters if they're available in the response
                if (work_sessions_completed !== undefined) {
                    const workCountEl = document.getElementById('work-sessions-count');
                    if (workCountEl) workCountEl.innerText = work_sessions_completed;
                }
                if (rest_sessions_completed !== undefined) {
                    const restCountEl = document.getElementById('rest-sessions-count');
                    if (restCountEl) restCountEl.innerText = rest_sessions_completed;
                }
                
                // Handle session transitions
                if (session_changed && session_complete) {
                    // Show completion message and notification
                    const completedSessionType = previous_session_was_work ? "work" : "rest";
                    const nextSessionType = is_work_session ? "work" : "rest";
                    
                    // Play completion sound
                    playCompletionSound();
                    
                    // Show browser notification
                    showBrowserNotification(
                        previous_session_was_work ? "Work session complete!" : "Rest break complete!",
                        previous_session_was_work ? "Time for a break! 🌱 Rest session starting..." : "Break's over! 💪 Work session starting..."
                    );
                    
                    // Update UI for new session type
                    updateSessionTypeDisplay(is_work_session, sessionTypeEl, progressCircle);
                    
                    // Show session transition message briefly
                    if (previous_session_was_work) {
                        pomodoroTimerEl.innerText = "Break Time!";
                        sessionTypeEl.innerText = "Work Complete! Starting Rest...";
                    } else {
                        pomodoroTimerEl.innerText = "Work Time!";
                        sessionTypeEl.innerText = "Rest Complete! Starting Work...";
                    }
                    
                    pomodoroTimerEl.className = "pomodoro-countdown completed";
                    progressCircle.style.strokeDashoffset = 0; // Complete the circle
                    
                    // After 2 seconds, switch to normal countdown display (timer is already running)
                    setTimeout(() => {
                        updateSessionTypeDisplay(is_work_session, sessionTypeEl, progressCircle);
                        
                        // The timer is already running, so just display the current time normally
                        // The next updatePomodoroTimer call will show the proper countdown
                        pomodoroTimerEl.className = "pomodoro-countdown";
                    }, 2000);
                    
                    return;
                }
                
                // Calculate total session duration for progress
                const totalDuration = is_work_session ? 
                    (parseInt(document.querySelector('#work_minutes')?.value) || 25) * 60 :
                    (parseInt(document.querySelector('#rest_minutes')?.value) || 5) * 60;
                
                // Calculate progress (0 to 1)
                const progress = Math.max(0, Math.min(1, (totalDuration - remaining_seconds) / totalDuration));
                
                // Calculate stroke-dashoffset for circular progress
                const radius = 120; // Match the radius from SVG
                const circumference = 2 * Math.PI * radius;
                const strokeDashoffset = circumference - (progress * circumference);
                
                // Update progress circle
                progressCircle.style.strokeDasharray = circumference;
                progressCircle.style.strokeDashoffset = strokeDashoffset;
                
                // Update session type display and colors
                updateSessionTypeDisplay(is_work_session, sessionTypeEl, progressCircle);

                // Format and display remaining time
                const minutes = Math.floor(remaining_seconds / 60);
                const seconds = remaining_seconds % 60;
                const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                
                pomodoroTimerEl.innerText = timeString;
                pomodoroTimerEl.className = "pomodoro-countdown";

                // Add visual feedback for last 10 seconds
                if (remaining_seconds <= 10 && remaining_seconds > 0 && is_running) {
                    pomodoroTimerEl.style.animation = 'pulse 0.5s infinite';
                } else {
                    pomodoroTimerEl.style.animation = '';
                }
            })
            .catch(err => {
                console.warn('Error fetching pomodoro time:', err);
                pomodoroTimerEl.innerText = "25:00";
                pomodoroTimerEl.className = "pomodoro-countdown";
                
                // Reset progress circle on error
                if (progressCircle) {
                    const radius = 120;
                    const circumference = 2 * Math.PI * radius;
                    progressCircle.style.strokeDashoffset = circumference;
                }
            });
    }

    function updateSessionTypeDisplay(is_work_session, sessionTypeEl, progressCircle) {
        if (is_work_session) {
            sessionTypeEl.innerText = "Work Session";
            sessionTypeEl.className = "session-type work-session";
            progressCircle.className = "progress-ring-fill work-session";
        } else {
            sessionTypeEl.innerText = "Rest Session";
            sessionTypeEl.className = "session-type rest-session";
            progressCircle.className = "progress-ring-fill rest-session";
        }
    }

    function playCompletionSound() {
        // Create a simple completion sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            console.log('Audio context not available');
        }
    }

    function showBrowserNotification(title, body) {
        // Request notification permission if not already granted
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '🍅',
                tag: 'pomodoro-timer'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, {
                        body: body,
                        icon: '🍅',
                        tag: 'pomodoro-timer'
                    });
                }
            });
        }
    }

    function initializePrioritySelects() {
        const prioritySelects = document.querySelectorAll('.priority-select');
        prioritySelects.forEach(select => {
            updatePrioritySelectBorder(select);
        });
    }

    function updatePrioritySelectBorder(select) {
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
            const priorityValue = parseInt(selectedOption.value);
            let borderColor = getPriorityColor(priorityValue);
            
            select.style.borderColor = borderColor;
            select.style.borderWidth = '2px';
        }
    }

    function getPriorityColor(priorityValue) {
        // Lower numbers = higher priority = redder colors
        switch(priorityValue) {
            case 1: return '#dc3545'; // Red - highest priority
            case 2: return '#fd7e14'; // Orange
            case 3: return '#ffc107'; // Yellow
            case 4: return '#20c997'; // Teal
            case 5: return '#28a745'; // Green - lowest priority
            default: return '#6c757d'; // Gray
        }
    }

    // Add event listeners for priority selects to update border colors
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('priority-select')) {
            updatePrioritySelectBorder(e.target);
        }
    });

    function updateAllTimers() {
        updateMainTimers();
        updateTaskDeadlineCountdowns();
    }

    function updateTaskDeadlineCountdowns() {
        const taskCountdowns = document.querySelectorAll('.task-countdown');
        const now = new Date();
        
        taskCountdowns.forEach(countdown => {
            const deadlineStr = countdown.getAttribute('data-deadline');
            if (!deadlineStr) return;
            
            const deadline = new Date(deadlineStr);
            const timeDiff = deadline - now;
            
            if (timeDiff <= 0) {
                countdown.innerText = "OVERDUE";
                countdown.classList.add('overdue-text');
            } else {
                countdown.classList.remove('overdue-text');
                
                const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
                
                if (hours > 0) {
                    countdown.innerText = `${hours}h ${minutes}m`;
                } else if (minutes > 0) {
                    countdown.innerText = `${minutes}m ${seconds}s`;
                } else {
                    countdown.innerText = `${seconds}s`;
                }
                
                // Add warning style when less than 15 minutes remaining
                if (timeDiff <= 15 * 60 * 1000) {
                    countdown.style.color = '#dc3545';
                    countdown.style.backgroundColor = '#fff3cd';
                    countdown.style.borderColor = '#ffc107';
                } else {
                    countdown.style.color = '#007BFF';
                    countdown.style.backgroundColor = '#f8f9fa';
                    countdown.style.borderColor = '#dee2e6';
                }
            }
        });
    }

    function updateMainTimers() {
        // 1) Main countdown
        if (!deadlineSet) {
            countdownEl.innerText = "--:--:--";
            spentTimeEl.innerText = "0:00";
            return;
        }
    
        fetch('/get_remaining_time')
            .then(r => r.text())
            .then(secondsStr => {
                let sec = parseInt(secondsStr);
                if (sec <= 0) {
                    countdownEl.innerText = "Time's up!";
                    countdownEl.classList.remove('low-time');
                    countdownEl.classList.add('all-done'); // Change to red when time is up
                } else {
                    // Calculate hours, minutes, seconds
                    let hrs = Math.floor(sec / 3600);
                    sec %= 3600;
                    let mins = Math.floor(sec / 60);
                    let secs = sec % 60;
    
                    // Toggle the red color when <= 900 seconds (15 minutes)
                    if (sec + mins * 60 + hrs * 3600 <= 900) {
                        countdownEl.classList.add('low-time');
                        countdownEl.classList.remove('all-done');
                    } else {
                        countdownEl.classList.remove('low-time');
                        countdownEl.classList.remove('all-done');
                    }
    
                    // Format the display
                    if (hrs < 1) {
                        const secsPadded = secs.toString().padStart(2, '0');
                        countdownEl.innerText = mins + ":" + secsPadded;
                    } else {
                        countdownEl.innerText = hrs + ":" + mins + ":" + secs;
                    }
                }
            })
            .catch(err => {
                console.warn('Error fetching remaining time:', err);
                countdownEl.innerText = "--:--:--";
            });
    
        // 2) Spent time (time since last completion or countdown start)
        fetch('/get_spent_time')
            .then(r => r.text())
            .then(spentStr => {
                let spent = parseInt(spentStr);
                if (spent < 0) {
                    spentTimeEl.innerText = "0:00";
                    return;
                }
                let hrs = Math.floor(spent / 3600);
                let remainder = spent % 3600;
                let mins = Math.floor(remainder / 60);
                let secs = remainder % 60;
    
                // If under an hour => M:SS
                if (hrs < 1) {
                    spentTimeEl.innerText = mins + ":" + secs.toString().padStart(2, '0');
                } else {
                    const minsStr = mins.toString().padStart(2, '0');
                    const secsStr = secs.toString().padStart(2, '0');
                    spentTimeEl.innerText = hrs + ":" + minsStr + ":" + secsStr;
                }
            })
            .catch(err => {
                console.warn('Error fetching spent time:', err);
                spentTimeEl.innerText = "0:00";
            });
    }
    
});

/**
 * Basic confetti animation
 */
function launchConfetti() {
    const duration = 3000;
    const end = Date.now() + duration;

    (function frame() {
        confetti({
            particleCount: 5,
            startVelocity: 30,
            spread: 360,
            ticks: 60,
            origin: {
                x: Math.random(),
                y: Math.random() - 0.2
            }
        });
        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    }());
}

/**
 * Utility function to show notifications (for future enhancements)
 */
function showNotification(message, type = 'info') {
    // This can be enhanced with a proper notification system
    console.log(`${type.toUpperCase()}: ${message}`);
}

/**
 * Add keyboard shortcuts for power users
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to quickly add task
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const taskInput = document.querySelector('input[name="task_text"]');
        if (taskInput && !taskInput.value.trim()) {
            taskInput.focus();
            e.preventDefault();
        }
    }
    
    // Escape to clear focused input
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === 'INPUT') {
            activeElement.blur();
        }
    }
});

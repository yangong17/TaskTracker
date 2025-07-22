document.addEventListener('DOMContentLoaded', () => {
    const countdownEl = document.getElementById('countdown');
    const spentTimeEl = document.getElementById('spent-time');

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

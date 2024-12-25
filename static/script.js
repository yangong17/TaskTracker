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

    setInterval(updateTimers, 1000);
    updateTimers();

    function updateTimers() {
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
                } else {
                    // Calculate hours, minutes, seconds
                    let hrs = Math.floor(sec / 3600);
                    sec %= 3600;
                    let mins = Math.floor(sec / 60);
                    let secs = sec % 60;
    
                    // Toggle the red color when <= 900 seconds (15 minutes)
                    if (sec + mins * 60 + hrs * 3600 <= 900) {
                        countdownEl.classList.add('low-time');
                    } else {
                        countdownEl.classList.remove('low-time');
                    }
    
                    // Format the display
                    if (hrs < 1) {
                        const secsPadded = secs.toString().padStart(2, '0');
                        countdownEl.innerText = mins + ":" + secsPadded;
                    } else {
                        countdownEl.innerText = hrs + ":" + mins + ":" + secs;
                    }
                }
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

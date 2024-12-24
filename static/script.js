document.addEventListener('DOMContentLoaded', () => {
    const countdownEl = document.getElementById('countdown');
    const spentTimeEl = document.getElementById('spent-time');

    // If all tasks complete, show "All tasks complete" in green and do not update timers
    if (allDone) {
        countdownEl.innerText = "All tasks complete";
        countdownEl.classList.add('all-done');
        spentTimeEl.innerText = "0:00";
        launchConfetti();
        return;
    }

    // Update both timers every second
    setInterval(updateTimers, 1000);
    updateTimers();

    function updateTimers() {
        // 1) Main countdown timer
        if (!deadlineSet) {
            countdownEl.innerText = "--:--:--";
            spentTimeEl.innerText = "0:00";
            return;
        }

        fetch('/get_remaining_time')
            .then(response => response.text())
            .then(secondsStr => {
                let sec = parseInt(secondsStr);
                if (sec <= 0) {
                    countdownEl.innerText = "Time's up!";
                    countdownEl.classList.remove('low-time');
                } else {
                    let hrs = Math.floor(sec / 3600);
                    sec %= 3600;
                    let mins = Math.floor(sec / 60);
                    let secs = sec % 60;

                    if (hrs < 1) {
                        // under 1 hour => M:SS
                        const secsPadded = secs.toString().padStart(2, '0');
                        countdownEl.innerText = mins + ":" + secsPadded;
                    } else {
                        // HH:MM:SS
                        countdownEl.innerText = hrs + ":" + mins + ":" + secs;
                    }

                    // If <= 15 minutes remain, turn red
                    if ((hrs * 3600 + mins * 60 + secs) <= 900) {
                        countdownEl.classList.add('low-time');
                    } else {
                        countdownEl.classList.remove('low-time');
                    }
                }
            });

        // 2) Spent time (time since last completion or countdown start)
        fetch('/get_spent_time')
            .then(response => response.text())
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

                // If no hours, just do M:SS
                if (hrs < 1) {
                    const secsStr = secs.toString().padStart(2, '0');
                    spentTimeEl.innerText = mins + ":" + secsStr;
                } else {
                    // If hours exist => HH:MM:SS
                    const minsStr = mins.toString().padStart(2, '0');
                    const secsStr = secs.toString().padStart(2, '0');
                    spentTimeEl.innerText = hrs + ":" + minsStr + ":" + secsStr;
                }
            });
    }
});

/**
 * Launch a brief confetti animation.
 */
function launchConfetti() {
    const duration = 3 * 1000;
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

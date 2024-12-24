document.addEventListener('DOMContentLoaded', () => {
    const countdownEl = document.getElementById('countdown');

    // If all tasks complete, show "All tasks complete" in green and do not update timer
    if (allDone) {
        countdownEl.innerText = "All tasks complete";
        countdownEl.classList.add('all-done');
        launchConfetti();
        return; // Stop any timer updates
    }

    function updateCountdown() {
        if (!deadlineSet) {
            // No deadline set, just show default
            countdownEl.innerText = "--:--:--";
            return;
        }

        fetch('/get_remaining_time')
        .then(response => response.text())
        .then(secondsStr => {
            let sec = parseInt(secondsStr);
            if (sec <= 0) {
                countdownEl.innerText = "Time's up!";
                countdownEl.classList.remove('low-time');
                return; // Stop updates
            }

            let hrs = Math.floor(sec / 3600);
            sec %= 3600;
            let mins = Math.floor(sec / 60);
            let secs = sec % 60;

            // If it's under an hour, display "M:SS"
            if (hrs < 1) {
                const secsPadded = secs.toString().padStart(2, '0');
                countdownEl.innerText = mins + ":" + secsPadded;
            } else {
                // Otherwise, display "Xh Xm Xs"
                countdownEl.innerText = hrs + ":" + mins + ":" + secs;
            }

            // If 15 minutes or less remain, turn timer red
            if ((hrs * 3600 + mins * 60 + secs) <= 900) {
                countdownEl.classList.add('low-time');
            } else {
                countdownEl.classList.remove('low-time');
            }
        });
    }

    setInterval(updateCountdown, 1000);
    updateCountdown();
});

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

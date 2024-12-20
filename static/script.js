function updateCountdown() {
    fetch('/get_remaining_time')
    .then(response => response.text())
    .then(seconds => {
        let sec = parseInt(seconds);
        let hrs = Math.floor(sec / 3600);
        sec %= 3600;
        let mins = Math.floor(sec / 60);
        let secs = sec % 60;
        document.getElementById('countdown').innerText =
            (hrs < 10 ? '0' : '') + hrs + ':' +
            (mins < 10 ? '0' : '') + mins + ':' +
            (secs < 10 ? '0' : '') + secs;
    });
}

// If all tasks complete, run confetti
function launchConfetti() {
    var duration = 3 * 1000;
    var end = Date.now() + duration;

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

document.addEventListener('DOMContentLoaded', () => {
    setInterval(updateCountdown, 1000);
    updateCountdown();

    if (allDone) {
        launchConfetti();
    }
});

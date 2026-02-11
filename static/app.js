// Peloton Cadence Monitor Dashboard JavaScript

function updateDashboard() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update current cadence
            document.getElementById('current-cadence').textContent = data.current_cadence;

            // Update average cadence
            const avgCadence = data.average_cadence.toFixed(1);
            document.getElementById('average-cadence').textContent = avgCadence;

            // Update YouTube status
            const youtubeIndicator = document.getElementById('youtube-indicator');
            const youtubeStatus = document.getElementById('youtube-status');

            if (data.youtube_blocked) {
                youtubeIndicator.className = 'indicator blocked';
                youtubeStatus.textContent = 'BLOCKED';
                youtubeStatus.className = 'status-text blocked';
            } else {
                youtubeIndicator.className = 'indicator allowed';
                youtubeStatus.textContent = 'ALLOWED';
                youtubeStatus.className = 'status-text allowed';
            }

            // Update sensor status
            const sensorDot = document.getElementById('sensor-dot');
            const sensorText = document.getElementById('sensor-text');

            if (data.sensor_connected) {
                sensorDot.className = 'dot connected';
                sensorText.textContent = 'Connected';
            } else {
                sensorDot.className = 'dot disconnected';
                sensorText.textContent = 'Disconnected';
            }

            // Update controller status
            const controllerDot = document.getElementById('controller-dot');
            const controllerText = document.getElementById('controller-text');

            if (data.controller_connected) {
                controllerDot.className = 'dot connected';
                controllerText.textContent = 'Connected';
            } else {
                controllerDot.className = 'dot disconnected';
                controllerText.textContent = 'Disconnected';
            }

            // Update last update time
            const lastUpdate = new Date(data.last_update * 1000);
            const now = new Date();
            const secondsAgo = Math.floor((now - lastUpdate) / 1000);

            let timeText;
            if (secondsAgo < 5) {
                timeText = 'Just now';
            } else if (secondsAgo < 60) {
                timeText = `${secondsAgo} seconds ago`;
            } else {
                const minutesAgo = Math.floor(secondsAgo / 60);
                timeText = `${minutesAgo} minute${minutesAgo > 1 ? 's' : ''} ago`;
            }

            document.getElementById('last-update').textContent = timeText;

            // Color code cadence cards based on threshold
            fetch('/api/config')
                .then(response => response.json())
                .then(config => {
                    const threshold = config.threshold;
                    const cadenceCard = document.getElementById('cadence-card');
                    const averageCard = document.getElementById('average-card');

                    if (data.average_cadence >= threshold) {
                        averageCard.style.borderLeft = '5px solid #10b981';
                    } else {
                        averageCard.style.borderLeft = '5px solid #ef4444';
                    }
                });
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            document.getElementById('last-update').textContent = 'Error';
        });
}

// Update dashboard every second
setInterval(updateDashboard, 1000);

// Initial update
updateDashboard();

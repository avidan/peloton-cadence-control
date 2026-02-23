// Peloton Cadence Monitor - Dashboard Application

(function () {
    'use strict';

    // --- DOM refs ---
    const el = {
        cadence: document.getElementById('current-cadence'),
        average: document.getElementById('average-cadence'),
        gaugeArc: document.getElementById('gauge-arc'),
        youtubeCard: document.getElementById('youtube-card'),
        youtubeStatus: document.getElementById('youtube-status'),
        sensorDot: document.getElementById('sensor-dot'),
        controllerDot: document.getElementById('controller-dot'),
        sessionTime: document.getElementById('session-time'),
        peakCadence: document.getElementById('peak-cadence'),
        percentAbove: document.getElementById('percent-above'),
        thresholdFill: document.getElementById('threshold-fill'),
        thresholdMarker: document.getElementById('threshold-marker'),
        thresholdInput: document.getElementById('threshold-input'),
        thresholdSave: document.getElementById('threshold-save'),
        thresholdLabel: document.querySelector('.threshold-label'),
        graceInput: document.getElementById('grace-input'),
        graceSave: document.getElementById('grace-save'),
        windowInput: document.getElementById('window-input'),
        windowSave: document.getElementById('window-save'),
        lastUpdate: document.getElementById('last-update'),
    };

    // Gauge constants: semicircle arc length
    const ARC_LENGTH = 251.3;
    const MAX_RPM = 120;

    // --- Chart.js setup ---
    let chart = null;

    function initChart() {
        const ctx = document.getElementById('cadence-chart');
        if (!ctx) return;

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Cadence',
                        data: [],
                        borderColor: '#00d4aa',
                        backgroundColor: 'rgba(0, 212, 170, 0.08)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        pointHitRadius: 6,
                    },
                    {
                        label: 'Threshold',
                        data: [],
                        borderColor: 'rgba(255, 71, 87, 0.5)',
                        borderWidth: 1,
                        borderDash: [6, 4],
                        fill: false,
                        pointRadius: 0,
                        pointHitRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                interaction: { intersect: false, mode: 'index' },
                scales: {
                    x: {
                        display: true,
                        grid: { color: 'rgba(100, 100, 150, 0.15)' },
                        ticks: {
                            color: '#555588',
                            font: { size: 10 },
                            maxTicksLimit: 10,
                            callback: function (val, idx, ticks) {
                                const v = this.getLabelForValue(val);
                                const sec = Math.round(parseFloat(v));
                                if (sec === 0) return 'now';
                                const m = Math.floor(Math.abs(sec) / 60);
                                const s = Math.abs(sec) % 60;
                                return m > 0 ? `-${m}m${s ? s + 's' : ''}` : `${sec}s`;
                            },
                        },
                    },
                    y: {
                        display: true,
                        min: 0,
                        suggestedMax: 120,
                        grid: { color: 'rgba(100, 100, 150, 0.15)' },
                        ticks: { color: '#555588', font: { size: 10 } },
                    },
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e1e3f',
                        titleColor: '#ccc',
                        bodyColor: '#fff',
                        borderColor: '#2a2a5a',
                        borderWidth: 1,
                        callbacks: {
                            label: function (ctx) {
                                return ctx.dataset.label + ': ' + ctx.parsed.y + ' RPM';
                            },
                        },
                    },
                },
            },
        });
    }

    // --- Update functions ---

    function updateGauge(rpm) {
        const clamped = Math.min(Math.max(rpm, 0), MAX_RPM);
        const ratio = clamped / MAX_RPM;
        const dashLen = ratio * ARC_LENGTH;
        el.gaugeArc.setAttribute('stroke-dasharray', dashLen + ' ' + ARC_LENGTH);

        // Color based on threshold from data attribute or default
        const threshold = parseInt(el.thresholdMarker.title.match(/\d+/)) || 60;
        if (rpm >= threshold) {
            el.gaugeArc.setAttribute('stroke', '#00d4aa');
        } else if (rpm >= threshold * 0.7) {
            el.gaugeArc.setAttribute('stroke', '#ffa502');
        } else {
            el.gaugeArc.setAttribute('stroke', '#ff4757');
        }
    }

    function updateThresholdDisplay(threshold) {
        el.thresholdMarker.title = 'Threshold: ' + threshold + ' RPM';
        if (el.thresholdLabel) {
            el.thresholdLabel.textContent = 'Threshold: ' + threshold + ' RPM';
        }
        // Sync input only if user isn't currently editing
        if (el.thresholdInput && document.activeElement !== el.thresholdInput) {
            el.thresholdInput.value = threshold;
        }
    }

    function updateStatus(data) {
        // Cadence
        el.cadence.textContent = data.current_cadence;
        updateGauge(data.current_cadence);

        // Average
        el.average.textContent = data.average_cadence.toFixed(1);

        // Update config displays from live data
        updateThresholdDisplay(data.threshold);
        syncConfigInputs(data);

        // Threshold bar (scale: 0-120 RPM range)
        const avgPct = Math.min(data.average_cadence / MAX_RPM * 100, 100);
        el.thresholdFill.style.width = avgPct + '%';
        if (data.average_cadence >= data.threshold) {
            el.thresholdFill.classList.remove('below');
        } else {
            el.thresholdFill.classList.add('below');
        }
        // Position threshold marker
        const markerPct = Math.min(data.threshold / MAX_RPM * 100, 100);
        el.thresholdMarker.style.left = markerPct + '%';

        // YouTube
        if (data.youtube_blocked) {
            el.youtubeCard.className = 'card youtube-card blocked';
            el.youtubeStatus.textContent = 'BLOCKED';
        } else {
            el.youtubeCard.className = 'card youtube-card allowed';
            el.youtubeStatus.textContent = 'ALLOWED';
        }

        // Connections
        el.sensorDot.className = 'dot ' + (data.sensor_connected ? 'connected' : 'disconnected');
        el.controllerDot.className = 'dot ' + (data.controller_connected ? 'connected' : 'disconnected');

        // Session timer
        const elapsed = Math.floor(Date.now() / 1000 - data.session_start);
        if (elapsed >= 0) {
            const m = Math.floor(elapsed / 60);
            const s = elapsed % 60;
            el.sessionTime.textContent = String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
        }

        // Session stats
        el.peakCadence.textContent = data.peak_cadence;
        el.percentAbove.textContent = data.percent_above_threshold + '%';

        // Last update
        const ago = Math.floor(Date.now() / 1000 - data.last_update);
        if (ago < 3) {
            el.lastUpdate.textContent = 'just now';
        } else if (ago < 60) {
            el.lastUpdate.textContent = ago + 's ago';
        } else {
            el.lastUpdate.textContent = Math.floor(ago / 60) + 'm ago';
        }
    }

    function updateChart(historyData) {
        if (!chart || !historyData.points) return;

        const points = historyData.points;
        const labels = points.map(function (p) { return p.t; });
        const cadenceData = points.map(function (p) { return p.c; });
        const thresholdData = points.map(function () { return historyData.threshold; });

        chart.data.labels = labels;
        chart.data.datasets[0].data = cadenceData;
        chart.data.datasets[1].data = thresholdData;
        chart.update('none');
    }

    // --- Polling ---

    function pollStatus() {
        fetch('/api/status')
            .then(function (r) { return r.json(); })
            .then(updateStatus)
            .catch(function (err) {
                console.error('Status poll error:', err);
                el.lastUpdate.textContent = 'connection lost';
            });
    }

    function pollHistory() {
        fetch('/api/history')
            .then(function (r) { return r.json(); })
            .then(updateChart)
            .catch(function (err) {
                console.error('History poll error:', err);
            });
    }

    // --- Config editing ---
    function saveConfig(fieldKey, inputEl, btnEl, min, max) {
        var value = parseInt(inputEl.value, 10);
        if (isNaN(value) || value < min || value > max) {
            inputEl.classList.add('input-error');
            setTimeout(function () { inputEl.classList.remove('input-error'); }, 1000);
            return;
        }
        btnEl.textContent = '...';
        btnEl.disabled = true;
        var body = {};
        body[fieldKey] = value;
        fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    btnEl.textContent = 'Error';
                } else {
                    if (data.threshold) updateThresholdDisplay(data.threshold);
                    syncConfigInputs(data);
                    btnEl.textContent = 'Saved!';
                }
                setTimeout(function () { btnEl.textContent = 'Save'; }, 1500);
            })
            .catch(function () {
                btnEl.textContent = 'Error';
                setTimeout(function () { btnEl.textContent = 'Save'; }, 1500);
            })
            .finally(function () {
                btnEl.disabled = false;
            });
    }

    function syncConfigInputs(data) {
        if (data.grace_period != null && document.activeElement !== el.graceInput) {
            el.graceInput.value = data.grace_period;
        }
        if (data.rolling_window != null && document.activeElement !== el.windowInput) {
            el.windowInput.value = data.rolling_window;
        }
    }

    // Threshold
    el.thresholdSave.addEventListener('click', function () {
        saveConfig('threshold', el.thresholdInput, el.thresholdSave, 1, 200);
    });
    el.thresholdInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') saveConfig('threshold', el.thresholdInput, el.thresholdSave, 1, 200);
    });

    // Grace period
    el.graceSave.addEventListener('click', function () {
        saveConfig('grace_period', el.graceInput, el.graceSave, 1, 60);
    });
    el.graceInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') saveConfig('grace_period', el.graceInput, el.graceSave, 1, 60);
    });

    // Rolling average window
    el.windowSave.addEventListener('click', function () {
        saveConfig('rolling_window', el.windowInput, el.windowSave, 1, 60);
    });
    el.windowInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') saveConfig('rolling_window', el.windowInput, el.windowSave, 1, 60);
    });

    // --- Init ---
    initChart();
    pollStatus();
    pollHistory();

    setInterval(pollStatus, 1000);
    setInterval(pollHistory, 3000);
})();

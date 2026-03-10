const notificationCooldown = new Map();
const sensorLastStatus = new Map();

function showNotification({
    type = 'info',
    title = 'Notification',
    message = '',
    sourceId = '',
    timestamp = null,
    dedupeKey = null,
    cooldownMs = 8000,
    durationMs = 6000
}) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const key = dedupeKey || `${type}:${sourceId}:${message}`;
    const now = Date.now();
    const lastShown = notificationCooldown.get(key);

    if (lastShown && now - lastShown < cooldownMs) return;
    notificationCooldown.set(key, now);

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    const readableTime = timestamp
        ? new Date(timestamp).toLocaleTimeString()
        : new Date().toLocaleTimeString();

    notification.innerHTML = `
        <div class="notification-close" onclick="this.parentElement.remove()">×</div>
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
        <div class="notification-meta">${sourceId ? `Source: ${sourceId} • ` : ''}${readableTime}</div>
    `;

    container.appendChild(notification);
    setTimeout(() => { if (notification.parentElement) notification.remove(); }, durationMs);
}


function notificationOnRuleTriggered(data) {
    const key = `rule_popup_${data.rule_id}`;
    showNotification({
        type: 'rule',
        title: 'Rule triggered',
        message: `${data.sensor_name} ${data.operator} ${data.sensor_target_value} → ${data.actuator_name} set to ${data.actuator_set_value}`,
        sourceId: data.sensor_name,
        timestamp: data.timestamp
    });
};

//connect
function notificationOnConnection() {
    console.log('Connesso al Server Flask (WebSockets)!');

    const alreadyShown = sessionStorage.getItem('frontend_connected_popup_shown');

    if (!alreadyShown) {
        showNotification({
            type: 'info',
            title: 'Frontend connected',
            message: 'WebSocket connection established successfully.',
            sourceId: 'frontend',
            durationMs: 4000
        });
        sessionStorage.setItem('frontend_connected_popup_shown', 'true');
    }
};

//

function notificationOnWarningStatus(data) {
    const sourceId = data.source_id;

    const currentStatus = (data.status || '').toLowerCase();
    const previousStatus = sensorLastStatus.get(sourceId);
    if (currentStatus === 'warning' && previousStatus !== 'warning') {
        showNotification({
            type: 'warning',
            title: '⚠ Sensor warning',
            message: `${sourceId} entered WARNING state.`,
            sourceId: sourceId,
            timestamp: data.timestamp
        });
    }
    sensorLastStatus.set(sourceId, currentStatus);
};
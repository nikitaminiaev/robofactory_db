function getCurrentModuleId() {
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    if (pathParts.length === 0) {
        return null;
    }
    return pathParts[pathParts.length - 1];
}

function setCadOutput(text) {
    const output = document.getElementById('cad-agent-output');
    output.textContent = text;
}

async function sendCadCommand() {
    const moduleId = getCurrentModuleId();
    if (!moduleId) {
        setCadOutput('Не удалось определить module_id из URL');
        return;
    }

    const message = document.getElementById('cad-command').value.trim();
    if (!message) {
        setCadOutput('Введите команду для выполнения.');
        return;
    }

    const button = document.getElementById('cad-send-btn');
    button.disabled = true;
    setCadOutput('Выполняю запрос...');

    try {
        const response = await fetch(`/api/modules/${moduleId}/cad-agent/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        if (!response.ok) {
            const detail = data.detail || 'Неизвестная ошибка';
            setCadOutput(`Ошибка: ${detail}`);
            return;
        }

        setCadOutput(JSON.stringify(data, null, 2));
    } catch (error) {
        setCadOutput(`Ошибка сети: ${error.message}`);
    } finally {
        button.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('cad-send-btn');
    if (!button) {
        return;
    }
    button.addEventListener('click', sendCadCommand);
});

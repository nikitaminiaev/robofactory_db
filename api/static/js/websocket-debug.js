/**
 * WebSocket Debug Script
 * Скрипт для отладки проблем с WebSocket сервером
 */

// Функция для добавления отладочных кнопок на страницу
function addDebugButtons() {
    // Проверяем, существует ли уже отладочная панель
    if (document.getElementById('websocket-debug-panel')) {
        return;
    }
    
    // Создаем отладочную панель
    const debugPanel = document.createElement('div');
    debugPanel.id = 'websocket-debug-panel';
    debugPanel.style.position = 'fixed';
    debugPanel.style.bottom = '50px';
    debugPanel.style.right = '10px';
    debugPanel.style.backgroundColor = '#f8f9fa';
    debugPanel.style.border = '1px solid #dee2e6';
    debugPanel.style.borderRadius = '4px';
    debugPanel.style.padding = '10px';
    debugPanel.style.zIndex = '1000';
    debugPanel.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
    
    // Добавляем заголовок
    const title = document.createElement('h5');
    title.textContent = 'Отладка WebSocket';
    title.style.marginTop = '0';
    title.style.marginBottom = '10px';
    debugPanel.appendChild(title);
    
    // Добавляем кнопки
    const buttons = [
        {
            id: 'debug-check-status',
            text: 'Проверить статус',
            action: checkServerStatusDebug
        },
        {
            id: 'debug-start-server',
            text: 'Запуск через fetch',
            action: startServerWithFetch
        },
        {
            id: 'debug-start-server-xhr',
            text: 'Запуск через XHR',
            action: startServerWithXHR
        },
        {
            id: 'debug-fix-ui',
            text: 'Исправить UI',
            action: fixUIBasedOnServerStatus
        },
        {
            id: 'debug-toggle-panel',
            text: 'Скрыть панель',
            action: toggleDebugPanel
        }
    ];
    
    buttons.forEach(btn => {
        const button = document.createElement('button');
        button.id = btn.id;
        button.textContent = btn.text;
        button.className = 'btn btn-sm btn-outline-secondary mb-2 mr-2';
        button.style.marginRight = '5px';
        button.style.marginBottom = '5px';
        button.addEventListener('click', btn.action);
        debugPanel.appendChild(button);
    });
    
    // Добавляем лог
    const log = document.createElement('div');
    log.id = 'debug-log';
    log.style.maxHeight = '150px';
    log.style.overflowY = 'auto';
    log.style.fontSize = '12px';
    log.style.backgroundColor = '#212529';
    log.style.color = '#f8f9fa';
    log.style.padding = '5px';
    log.style.borderRadius = '4px';
    log.style.marginTop = '10px';
    debugPanel.appendChild(log);
    
    // Добавляем панель на страницу
    document.body.appendChild(debugPanel);
    
    // Добавляем сообщение в лог
    debugLog('Отладочная панель инициализирована');
}

// Функция для добавления сообщений в отладочный лог
function debugLog(message) {
    const log = document.getElementById('debug-log');
    if (log) {
        const entry = document.createElement('div');
        entry.innerHTML = `<span style="color: #6c757d;">[${new Date().toLocaleTimeString()}]</span> ${message}`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }
    console.log('[WebSocket Debug]', message);
}

// Функция для проверки статуса сервера (отладочная версия)
async function checkServerStatusDebug() {
    debugLog('Проверка статуса сервера (отладочная версия)...');
    
    try {
        const response = await fetch('/api/websocket/status');
        const data = await response.json();
        
        debugLog(`Статус сервера: ${data.running ? 'Запущен' : 'Остановлен'}`);
        
        // Проверяем, соответствует ли UI текущему статусу
        const statusElement = document.getElementById('server-status');
        const startButton = document.getElementById('start-server');
        const stopButton = document.getElementById('stop-server');
        
        if (statusElement && startButton && stopButton) {
            const uiShowsRunning = statusElement.textContent.includes('Запущен');
            const startButtonDisabled = startButton.disabled;
            const stopButtonDisabled = stopButton.disabled;
            
            debugLog(`UI показывает: ${uiShowsRunning ? 'Запущен' : 'Остановлен'}`);
            debugLog(`Кнопка "Запустить" ${startButtonDisabled ? 'отключена' : 'активна'}`);
            debugLog(`Кнопка "Остановить" ${stopButtonDisabled ? 'отключена' : 'активна'}`);
            
            if (data.running !== uiShowsRunning) {
                debugLog('ОШИБКА: Несоответствие между реальным статусом и UI!');
                
                // Принудительно обновляем UI
                if (typeof updateUIBasedOnServerStatus === 'function') {
                    debugLog('Принудительное обновление UI...');
                    updateUIBasedOnServerStatus(data.running);
                } else {
                    debugLog('Функция updateUIBasedOnServerStatus не найдена. Используем ручное обновление UI.');
                    fixUIBasedOnServerStatus();
                }
            }
        }
        
        return data.running;
    } catch (error) {
        debugLog(`Ошибка при проверке статуса: ${error.message}`);
        return false;
    }
}

// Функция для принудительного обновления UI на основе реального статуса сервера
async function fixUIBasedOnServerStatus() {
    debugLog('Принудительное обновление UI на основе реального статуса сервера...');
    
    try {
        const response = await fetch('/api/websocket/status');
        const data = await response.json();
        
        debugLog(`Получен статус сервера: ${data.running ? 'Запущен' : 'Остановлен'}`);
        
        // Обновляем UI вручную
        const statusElement = document.getElementById('server-status');
        const startButton = document.getElementById('start-server');
        const stopButton = document.getElementById('stop-server');
        
        if (statusElement && startButton && stopButton) {
            if (data.running) {
                // Сервер запущен
                statusElement.textContent = 'Статус сервера: Запущен';
                statusElement.className = 'alert alert-success';
                startButton.disabled = true;
                stopButton.disabled = false;
                
                // Обновляем глобальную переменную, если она существует
                if (typeof serverRunning !== 'undefined') {
                    serverRunning = true;
                    debugLog('Обновлена глобальная переменная serverRunning = true');
                }
                
                // Запускаем обновление клиентов, если функция существует
                if (typeof updateClientsInfo === 'function') {
                    updateClientsInfo();
                    debugLog('Вызвана функция updateClientsInfo()');
                    
                    // Запускаем интервал обновления клиентов, если он не запущен
                    if (typeof clientsUpdateInterval !== 'undefined' && !clientsUpdateInterval) {
                        clientsUpdateInterval = setInterval(updateClientsInfo, 5000);
                        debugLog('Запущен интервал обновления клиентов');
                    }
                }
                
                // Запускаем обновление сообщений, если функция существует
                if (typeof updateMessages === 'function') {
                    updateMessages();
                    debugLog('Вызвана функция updateMessages()');
                    
                    // Запускаем интервал обновления сообщений, если он не запущен
                    if (typeof messagesUpdateInterval !== 'undefined' && !messagesUpdateInterval) {
                        messagesUpdateInterval = setInterval(updateMessages, 3000);
                        debugLog('Запущен интервал обновления сообщений');
                    }
                }
                
                debugLog('UI обновлен: сервер запущен');
            } else {
                // Сервер остановлен
                statusElement.textContent = 'Статус сервера: Остановлен';
                statusElement.className = 'alert alert-warning';
                startButton.disabled = false;
                stopButton.disabled = true;
                
                // Обновляем глобальную переменную, если она существует
                if (typeof serverRunning !== 'undefined') {
                    serverRunning = false;
                    debugLog('Обновлена глобальная переменная serverRunning = false');
                }
                
                // Останавливаем интервал обновления клиентов, если он запущен
                if (typeof clientsUpdateInterval !== 'undefined' && clientsUpdateInterval) {
                    clearInterval(clientsUpdateInterval);
                    clientsUpdateInterval = null;
                    debugLog('Остановлен интервал обновления клиентов');
                }
                
                // Останавливаем интервал обновления сообщений, если он запущен
                if (typeof messagesUpdateInterval !== 'undefined' && messagesUpdateInterval) {
                    clearInterval(messagesUpdateInterval);
                    messagesUpdateInterval = null;
                    debugLog('Остановлен интервал обновления сообщений');
                }
                
                // Обновляем информацию о клиентах
                const clientsInfoElement = document.getElementById('clients-info');
                if (clientsInfoElement) {
                    clientsInfoElement.textContent = 'Сервер не запущен';
                    clientsInfoElement.className = 'alert alert-warning mt-2';
                }
                
                debugLog('UI обновлен: сервер остановлен');
            }
            
            // Добавляем сообщение в лог сообщений, если функция существует
            if (typeof addMessage === 'function') {
                addMessage(`UI принудительно обновлен. Статус сервера: ${data.running ? 'Запущен' : 'Остановлен'}`);
                debugLog('Добавлено сообщение в лог сообщений');
            }
        } else {
            debugLog('Не удалось найти элементы UI для обновления');
        }
    } catch (error) {
        debugLog(`Ошибка при обновлении UI: ${error.message}`);
    }
}

// Функция для запуска сервера через fetch API
async function startServerWithFetch() {
    debugLog('Запуск сервера через fetch API...');
    
    try {
        const response = await fetch('/api/websocket/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        debugLog(`Статус ответа: ${response.status} ${response.statusText}`);
        
        const data = await response.json();
        debugLog(`Ответ сервера: ${JSON.stringify(data)}`);
        
        if (data.success) {
            debugLog('Сервер успешно запущен через fetch API');
            
            // Обновляем UI
            if (typeof checkServerStatus === 'function') {
                checkServerStatus();
            } else {
                fixUIBasedOnServerStatus();
            }
        } else {
            debugLog(`Ошибка при запуске сервера: ${data.message}`);
        }
    } catch (error) {
        debugLog(`Ошибка при запуске сервера через fetch: ${error.message}`);
    }
}

// Функция для запуска сервера через XMLHttpRequest
function startServerWithXHR() {
    debugLog('Запуск сервера через XMLHttpRequest...');
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/websocket/start', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    xhr.onreadystatechange = function() {
        debugLog(`XHR readyState: ${xhr.readyState}, status: ${xhr.status}`);
        
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    debugLog(`Ответ сервера: ${JSON.stringify(data)}`);
                    
                    if (data.success) {
                        debugLog('Сервер успешно запущен через XMLHttpRequest');
                        
                        // Обновляем UI
                        if (typeof checkServerStatus === 'function') {
                            checkServerStatus();
                        } else {
                            fixUIBasedOnServerStatus();
                        }
                    } else {
                        debugLog(`Ошибка при запуске сервера: ${data.message}`);
                    }
                } catch (e) {
                    debugLog(`Ошибка при разборе ответа: ${e.message}`);
                }
            } else {
                debugLog(`Ошибка HTTP: ${xhr.status}`);
            }
        }
    };
    
    xhr.onerror = function() {
        debugLog('Ошибка сети при запросе');
    };
    
    xhr.send();
    debugLog('Запрос на запуск сервера отправлен через XMLHttpRequest');
}

// Функция для скрытия/показа отладочной панели
function toggleDebugPanel() {
    const panel = document.getElementById('websocket-debug-panel');
    const log = document.getElementById('debug-log');
    const button = document.getElementById('debug-toggle-panel');
    
    if (log.style.display === 'none') {
        log.style.display = 'block';
        button.textContent = 'Скрыть панель';
    } else {
        log.style.display = 'none';
        button.textContent = 'Показать панель';
    }
}

// Функция для проверки работоспособности кнопок
function checkButtonsFunctionality() {
    debugLog('Проверка работоспособности кнопок...');
    
    const startButton = document.getElementById('start-server');
    const stopButton = document.getElementById('stop-server');
    const refreshButton = document.getElementById('force-refresh-status');
    
    if (startButton && stopButton && refreshButton) {
        // Проверяем, есть ли обработчики событий
        const startHasListener = startButton.onclick !== null || startButton._events || startButton._listeners;
        const stopHasListener = stopButton.onclick !== null || stopButton._events || stopButton._listeners;
        const refreshHasListener = refreshButton.onclick !== null || refreshButton._events || refreshButton._listeners;
        
        debugLog(`Кнопка "Запустить" имеет обработчик: ${startHasListener ? 'Да' : 'Нет'}`);
        debugLog(`Кнопка "Остановить" имеет обработчик: ${stopHasListener ? 'Да' : 'Нет'}`);
        debugLog(`Кнопка "Обновить статус" имеет обработчик: ${refreshHasListener ? 'Да' : 'Нет'}`);
        
        // Если обработчики отсутствуют, добавляем их
        if (!startHasListener) {
            debugLog('Добавление обработчика для кнопки "Запустить сервер"');
            startButton.onclick = function() {
                debugLog('Кнопка "Запустить сервер" нажата (добавленный обработчик)');
                startServerWithXHR();
            };
        }
        
        if (!stopHasListener) {
            debugLog('Добавление обработчика для кнопки "Остановить сервер"');
            stopButton.onclick = async function() {
                debugLog('Кнопка "Остановить сервер" нажата (добавленный обработчик)');
                
                try {
                    // Отключаем кнопку на время запроса
                    stopButton.disabled = true;
                    stopButton.textContent = 'Остановка...';
                    
                    const response = await fetch('/api/websocket/stop', {
                        method: 'POST'
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        debugLog('Сервер успешно остановлен');
                        fixUIBasedOnServerStatus();
                    } else {
                        debugLog(`Ошибка при остановке сервера: ${data.message}`);
                        stopButton.disabled = false;
                        stopButton.textContent = 'Остановить сервер';
                    }
                } catch (error) {
                    debugLog(`Ошибка при остановке сервера: ${error.message}`);
                    stopButton.disabled = false;
                    stopButton.textContent = 'Остановить сервер';
                }
            };
        }
        
        if (!refreshHasListener) {
            debugLog('Добавление обработчика для кнопки "Обновить статус"');
            refreshButton.onclick = function() {
                debugLog('Кнопка "Обновить статус" нажата (добавленный обработчик)');
                checkServerStatusDebug();
            };
        }
        
        // Добавляем дополнительные обработчики для отладки
        if (!startButton._debugListenerAdded) {
            startButton.addEventListener('click', function() {
                debugLog('Кнопка "Запустить сервер" нажата');
            });
            startButton._debugListenerAdded = true;
        }
        
        if (!stopButton._debugListenerAdded) {
            stopButton.addEventListener('click', function() {
                debugLog('Кнопка "Остановить сервер" нажата');
            });
            stopButton._debugListenerAdded = true;
        }
        
        if (!refreshButton._debugListenerAdded) {
            refreshButton.addEventListener('click', function() {
                debugLog('Кнопка "Обновить статус" нажата');
            });
            refreshButton._debugListenerAdded = true;
        }
    } else {
        debugLog('Не удалось найти все кнопки на странице');
    }
}

// Инициализация отладочного скрипта
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем небольшую задержку, чтобы убедиться, что страница полностью загружена
    setTimeout(function() {
        addDebugButtons();
        checkButtonsFunctionality();
        
        // Проверяем статус сервера
        checkServerStatusDebug();
        
        // Добавляем обработчик для кнопки "Запустить сервер" в обход стандартного
        const startButton = document.getElementById('start-server');
        if (startButton) {
            startButton.addEventListener('dblclick', function(e) {
                e.preventDefault();
                e.stopPropagation();
                debugLog('Двойной клик по кнопке "Запустить сервер" - принудительный запуск через XHR');
                startServerWithXHR();
            });
        }
    }, 1000);
}); 
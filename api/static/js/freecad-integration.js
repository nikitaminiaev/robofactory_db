/**
 * FreeCad Integration Script
 * Обрабатывает взаимодействие с FreeCad на всех страницах приложения
 */

// Глобальные переменные для отслеживания состояния сервера и клиентов
let serverRunning = false;
let connectedClientsCount = 0;
let checkStatusInterval = null;

// Функция для инициализации обработчиков событий кнопок FreeCad
function initFreeCadButtons() {
    // Сначала проверяем статус сервера и клиентов
    checkServerAndClientsStatus();
    
    // Запускаем периодическую проверку статуса
    if (!checkStatusInterval) {
        checkStatusInterval = setInterval(checkServerAndClientsStatus, 3000); // Проверяем каждые 3 секунды
    }
    
    console.log('FreeCad integration initialized');
}

// Функция для проверки статуса сервера и клиентов
async function checkServerAndClientsStatus() {
    try {
        // Проверяем статус сервера
        const serverResponse = await fetch('/api/websocket/status');
        const serverData = await serverResponse.json();
        
        // Обновляем глобальную переменную
        const previousServerRunning = serverRunning;
        serverRunning = serverData.running;
        
        // Если сервер запущен, проверяем количество клиентов
        if (serverRunning) {
            const clientsResponse = await fetch('/api/websocket/clients');
            const clientsData = await clientsResponse.json();
            
            // Обновляем глобальную переменную
            const previousClientsCount = connectedClientsCount;
            connectedClientsCount = clientsData.count || 0;
            
            // Логируем изменения в количестве клиентов
            if (previousClientsCount !== connectedClientsCount) {
                console.log(`Изменение количества клиентов: ${previousClientsCount} -> ${connectedClientsCount}`);
            }
        } else {
            connectedClientsCount = 0;
        }
        
        // Логируем изменения в статусе сервера
        if (previousServerRunning !== serverRunning) {
            console.log(`Изменение статуса сервера: ${previousServerRunning ? 'запущен' : 'остановлен'} -> ${serverRunning ? 'запущен' : 'остановлен'}`);
        }
        
        // Обновляем видимость кнопок на основе полученной информации
        updateFreeCadButtonsVisibility();
        
    } catch (error) {
        console.error('Ошибка при проверке статуса сервера и клиентов:', error);
        serverRunning = false;
        connectedClientsCount = 0;
        updateFreeCadButtonsVisibility();
    }
}

// Функция для обновления видимости кнопок FreeCad
function updateFreeCadButtonsVisibility() {
    // Находим все кнопки для загрузки во FreeCad на странице
    document.querySelectorAll('.load-freecad-btn').forEach(button => {
        if (serverRunning && connectedClientsCount > 0) {
            // Показываем кнопку и применяем стили
            button.style.display = 'inline-block';
            applyFreeCadButtonStyle(button);
            
            // Добавляем обработчик события клика, если его еще нет
            if (!button.hasAttribute('data-initialized')) {
                button.setAttribute('data-initialized', 'true');
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const objectId = this.getAttribute('data-id');
                    loadObjectToFreeCad(objectId);
                });
            }
        } else {
            // Скрываем кнопку
            button.style.display = 'none';
        }
    });
    
    // Добавляем информационное сообщение о статусе сервера и клиентах
    updateStatusMessage();
}

// Функция для добавления информационного сообщения о статусе сервера и клиентах
function updateStatusMessage() {
    // Проверяем, существует ли уже информационное сообщение
    let statusMessage = document.getElementById('freecad-status-message');
    
    if (!statusMessage) {
        // Создаем новый элемент для отображения статуса
        statusMessage = document.createElement('div');
        statusMessage.id = 'freecad-status-message';
        statusMessage.style.position = 'fixed';
        statusMessage.style.bottom = '10px';
        statusMessage.style.left = '10px';
        statusMessage.style.padding = '5px 10px';
        statusMessage.style.borderRadius = '4px';
        statusMessage.style.fontSize = '12px';
        statusMessage.style.zIndex = '9999';
        document.body.appendChild(statusMessage);
    }
    
    // Обновляем содержимое и стиль сообщения в зависимости от статуса
    if (!serverRunning) {
        statusMessage.textContent = 'WebSocket-сервер не запущен';
        statusMessage.style.backgroundColor = '#f8d7da';
        statusMessage.style.color = '#721c24';
        statusMessage.style.border = '1px solid #f5c6cb';
    } else if (connectedClientsCount === 0) {
        statusMessage.textContent = 'WebSocket-сервер запущен, но нет подключенных клиентов';
        statusMessage.style.backgroundColor = '#fff3cd';
        statusMessage.style.color = '#856404';
        statusMessage.style.border = '1px solid #ffeeba';
    } else {
        statusMessage.textContent = `WebSocket-сервер запущен, подключено клиентов: ${connectedClientsCount}`;
        statusMessage.style.backgroundColor = '#d4edda';
        statusMessage.style.color = '#155724';
        statusMessage.style.border = '1px solid #c3e6cb';
    }
}

// Функция для стилизации кнопок FreeCad
function applyFreeCadButtonStyle(button) {
    button.style.marginLeft = '10px';
    button.style.padding = '3px 8px';
    button.style.backgroundColor = '#4CAF50';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.cursor = 'pointer';
    button.style.transition = 'background-color 0.3s';
    
    // Добавляем эффект наведения
    button.addEventListener('mouseover', function() {
        this.style.backgroundColor = '#45a049';
    });
    
    button.addEventListener('mouseout', function() {
        this.style.backgroundColor = '#4CAF50';
    });
}

// Функция для загрузки объекта во FreeCad
function loadObjectToFreeCad(objectId) {
    // Проверяем статус сервера и клиентов перед отправкой запроса
    if (!serverRunning || connectedClientsCount === 0) {
        alert('Невозможно загрузить объект во FreeCad: WebSocket-сервер не запущен или нет подключенных клиентов.');
        return;
    }
    
    // Показываем индикатор загрузки или сообщение
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'loading-message';
    loadingMessage.textContent = 'Отправка запроса на загрузку во FreeCad...';
    loadingMessage.style.position = 'fixed';
    loadingMessage.style.top = '50%';
    loadingMessage.style.left = '50%';
    loadingMessage.style.transform = 'translate(-50%, -50%)';
    loadingMessage.style.padding = '15px';
    loadingMessage.style.backgroundColor = '#f8f9fa';
    loadingMessage.style.border = '1px solid #dee2e6';
    loadingMessage.style.borderRadius = '4px';
    loadingMessage.style.zIndex = '1000';
    document.body.appendChild(loadingMessage);

    console.log(`Отправка запроса на загрузку объекта ${objectId} во FreeCad`);
    
    // Делаем запрос к API
    fetch(`/api/basic_object/${objectId}/load_freecad`, {
        method: 'POST'
    })
    .then(response => {
        console.log('Получен ответ:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Данные ответа:', data);
        // Формируем подробное сообщение
        let messageLines = [];
        
        if (data.success) {
            messageLines.push('✅ Запрос успешно обработан');
            messageLines.push(`📋 ID объекта: ${data.object_id}`);
        } else {
            messageLines.push('❌ Ошибка при обработке запроса');
        }
        
        // Добавляем информацию о статусе WebSocket-сервера
        if (data.socket_server_running) {
            messageLines.push('✅ WebSocket-сервер запущен');
            
            if (data.message_sent) {
                messageLines.push('✅ Команда успешно отправлена во FreeCad');
            } else {
                messageLines.push('❌ Не удалось отправить команду во FreeCad');
                messageLines.push('👉 Проверьте, запущен ли FreeCad и подключен ли он к серверу');
            }
        } else {
            messageLines.push('❌ WebSocket-сервер не запущен');
            messageLines.push('👉 Запустите WebSocket-сервер через API: /api/websocket/start');
        }
        
        // Показываем сообщение пользователю
        document.body.removeChild(loadingMessage);
        alert(messageLines.join('\n'));
    })
    .catch(error => {
        console.error('Ошибка при загрузке объекта:', error);
        document.body.removeChild(loadingMessage);
        alert(`Произошла ошибка при загрузке объекта во FreeCad:\n${error.message}`);
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initFreeCadButtons();
    
    // Наблюдатель DOM для динамически добавляемых кнопок
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Если были добавлены новые элементы, обновляем видимость кнопок
                updateFreeCadButtonsVisibility();
            }
        });
    });
    
    // Наблюдаем за изменениями в DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}); 
/**
 * FreeCad Integration Script
 * Обрабатывает взаимодействие с FreeCad на всех страницах приложения
 */

// Функция для инициализации обработчиков событий кнопок FreeCad
function initFreeCadButtons() {
    // Находим все кнопки для загрузки во FreeCad на странице
    document.querySelectorAll('.load-freecad-btn').forEach(button => {
        // Применяем единый стиль ко всем кнопкам
        applyFreeCadButtonStyle(button);
        
        // Добавляем обработчик события клика
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const objectId = this.getAttribute('data-id');
            loadObjectToFreeCad(objectId);
        });
    });
    
    console.log('FreeCad integration buttons initialized');
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
    
    // Можно добавить наблюдатель DOM для динамически добавляемых кнопок
    // Это полезно, если контент загружается асинхронно
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Проверяем, были ли добавлены новые кнопки
                const newButtons = document.querySelectorAll('.load-freecad-btn:not([data-initialized])');
                if (newButtons.length > 0) {
                    newButtons.forEach(button => {
                        button.setAttribute('data-initialized', 'true');
                        applyFreeCadButtonStyle(button);
                        button.addEventListener('click', function(e) {
                            e.preventDefault();
                            const objectId = this.getAttribute('data-id');
                            loadObjectToFreeCad(objectId);
                        });
                    });
                    console.log(`Initialized ${newButtons.length} new FreeCad buttons`);
                }
            }
        });
    });
    
    // Наблюдаем за изменениями в DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}); 
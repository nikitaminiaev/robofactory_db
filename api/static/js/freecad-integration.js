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
    const connected = serverRunning && connectedClientsCount > 0;

    // Load FreeCad кнопки — в таблицах поиска и списках
    document.querySelectorAll('.load-freecad-btn').forEach(button => {
        if (connected) {
            button.style.display = 'inline-block';
            applyFreeCadButtonStyle(button);

            // Убираем поле depth если оно есть (старый код)
            let depthInput = button.nextElementSibling;
            if (depthInput && depthInput.classList.contains('freecad-depth-input')) {
                depthInput.remove();
            }

            if (!button.hasAttribute('data-initialized')) {
                button.setAttribute('data-initialized', 'true');
                
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const objectId = this.getAttribute('data-id');
                    // Проверяем, есть ли функция getChildDepthsForApi и таблица children
                    let childDepths = [];
                    if (typeof getChildDepthsForApi === 'function') {
                        const childrenTable = document.querySelector('.children-table');
                        if (childrenTable) {
                            childDepths = getChildDepthsForApi();
                        }
                    }
                    loadObjectToFreeCad(objectId, childDepths);
                });
            }
        } else {
            button.style.display = 'none';
        }
    });

    // Кнопки действий FreeCAD на странице деталей (Save, To Supersystem, To Subsystem)
    document.querySelectorAll('.freecad-action-btn').forEach(el => {
        el.style.display = connected ? 'inline-block' : 'none';
    });

    // Разделитель между обычными кнопками и кнопками FreeCAD
    const sep = document.getElementById('freecad-btn-separator');
    if (sep) sep.style.display = connected ? 'inline-block' : 'none';

    // Wire-up кнопок действий (однократно)
    _initFreeCadActionButtons();

    // Добавляем информационное сообщение о статусе сервера и клиентах
    updateStatusMessage();
}

function _initFreeCadActionButtons() {
    const saveBrepBtn = document.getElementById('btn-fc-save-brep');
    if (saveBrepBtn && !saveBrepBtn.hasAttribute('data-initialized')) {
        saveBrepBtn.setAttribute('data-initialized', 'true');
        saveBrepBtn.addEventListener('click', function(e) {
            e.preventDefault();
            saveBrepToFreeCad(this.getAttribute('data-id'));
        });
    }

    const savePosBtn = document.getElementById('btn-fc-save-position');
    if (savePosBtn && !savePosBtn.hasAttribute('data-initialized')) {
        savePosBtn.setAttribute('data-initialized', 'true');
        savePosBtn.addEventListener('click', function(e) {
            e.preventDefault();
            savePositionToFreeCad(this.getAttribute('data-id'));
        });
    }
}

// ── localStorage history tracking ──────────────────────────────────────────

function trackVisitedModule(moduleId) {
    if (!moduleId) return;
    const key = 'plm_visited_modules';
    const history = JSON.parse(localStorage.getItem(key) || '[]');
    const filtered = history.filter(id => id !== moduleId);
    filtered.unshift(moduleId);
    localStorage.setItem(key, JSON.stringify(filtered.slice(0, 100)));
}

function getLastVisitedFrom(ids) {
    const key = 'plm_visited_modules';
    const history = JSON.parse(localStorage.getItem(key) || '[]');
    for (const id of history) {
        if (ids.includes(id)) return id;
    }
    return null;
}

// ── Last Supersystem / Last Subsystem ──────────────────────────────────────

function initLastNavButtons() {
    const superBtn = document.getElementById('btn-last-supersystem');
    if (superBtn && !superBtn.hasAttribute('data-initialized')) {
        superBtn.setAttribute('data-initialized', 'true');
        superBtn.addEventListener('click', function(e) {
            e.preventDefault();
            goToLastSupersystem();
        });
    }

    const subBtn = document.getElementById('btn-last-subsystem');
    if (subBtn && !subBtn.hasAttribute('data-initialized')) {
        subBtn.setAttribute('data-initialized', 'true');
        subBtn.addEventListener('click', function(e) {
            e.preventDefault();
            goToLastSubsystem();
        });
    }
}

function goToLastSupersystem() {
    const data    = window.currentObjectData || {};
    const parents = data.parents || [];

    if (!parents.length) {
        showNotification('У данного модуля нет родителей', 'info');
        return;
    }

    const target = parents.length === 1
        ? parents[0]
        : getLastVisitedFrom(parents);

    if (target) {
        window.location.href = `/basic_object/${target}`;
        return;
    }

    showNotification('Несколько родителей — выберите нужный в списке Parents ниже', 'info');
    const el = document.getElementById('parentsList');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function goToLastSubsystem() {
    const data     = window.currentObjectData || {};
    const children = data.children || [];

    if (!children.length) {
        showNotification('У данного модуля нет дочерних объектов', 'info');
        return;
    }

    const target = children.length === 1
        ? children[0]
        : getLastVisitedFrom(children);

    if (target) {
        window.location.href = `/basic_object/${target}`;
        return;
    }

    showNotification('Несколько дочерних объектов — выберите нужный в списке Children ниже', 'info');
    const el = document.getElementById('childrenList');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
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
function loadObjectToFreeCad(objectId, childDepths = []) {
    // Проверяем статус сервера и клиентов перед отправкой запроса
    if (!serverRunning || connectedClientsCount === 0) {
        showNotification('Невозможно загрузить объект во FreeCad: WebSocket-сервер не запущен или нет подключенных клиентов.', 'error');
        return;
    }
    
    // Показываем индикатор загрузки
    showNotification('Отправка запроса на загрузку во FreeCad...', 'info');

    console.log(`Отправка запроса на загрузку объекта ${objectId} во FreeCad с childDepths:`, childDepths);
    
    // Формируем тело запроса
    const requestBody = {
        child_depths: childDepths
    };
    
    // Делаем запрос к API
    fetch(`/api/basic_object/${objectId}/load_freecad`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
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
    })
    .catch(error => {
        console.error('Ошибка при загрузке объекта:', error);
        showNotification(`Ошибка при загрузке объекта во FreeCad: ${error.message}`, 'error');
    });
}

// Функция для показа временного уведомления
function showNotification(message, type = 'info') {
    // Удаляем предыдущие уведомления
    const existingNotification = document.getElementById('temp-notification');
    if (existingNotification) {
        document.body.removeChild(existingNotification);
    }
    
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.id = 'temp-notification';
    notification.textContent = message;
    
    // Стили в зависимости от типа уведомления
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.padding = '10px 15px';
    notification.style.borderRadius = '4px';
    notification.style.zIndex = '10000';
    notification.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    notification.style.transition = 'opacity 0.5s';
    
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#d4edda';
            notification.style.color = '#155724';
            notification.style.border = '1px solid #c3e6cb';
            break;
        case 'error':
            notification.style.backgroundColor = '#f8d7da';
            notification.style.color = '#721c24';
            notification.style.border = '1px solid #f5c6cb';
            break;
        case 'info':
        default:
            notification.style.backgroundColor = '#e2f3f7';
            notification.style.color = '#0c5460';
            notification.style.border = '1px solid #bee5eb';
            break;
    }
    
    // Добавляем уведомление на страницу
    document.body.appendChild(notification);
    
    // Автоматически удаляем уведомление через 3 секунды
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 500);
        }
    }, 1000);
}

function saveBrepToFreeCad(moduleId) {
    if (!serverRunning || connectedClientsCount === 0) {
        showNotification('FreeCAD не подключён', 'error');
        return;
    }

    showNotification('Отправка команды Save BREP во FreeCAD...', 'info');

    fetch(`/api/basic_object/${moduleId}/freecad/save_brep`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showNotification('BREP сохранён', 'success');
            } else {
                showNotification(data.detail || 'Ошибка при сохранении BREP', 'error');
            }
        })
        .catch(err => showNotification(`Ошибка сети: ${err.message}`, 'error'));
}

function savePositionToFreeCad(moduleId) {
    if (!serverRunning || connectedClientsCount === 0) {
        showNotification('FreeCAD не подключён', 'error');
        return;
    }

    showNotification('Отправка команды Save Position во FreeCAD...', 'info');

    fetch(`/api/basic_object/${moduleId}/freecad/save_position`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showNotification('Позиция сохранена', 'success');
            } else {
                showNotification(data.detail || 'Ошибка при сохранении позиции', 'error');
            }
        })
        .catch(err => showNotification(`Ошибка сети: ${err.message}`, 'error'));
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    if (window._freecadIntegrationInitialized) {
        return;
    }
    window._freecadIntegrationInitialized = true;
    
    initFreeCadButtons();
    
    // Наблюдатель DOM для динамически добавляемых кнопок
    const observer = new MutationObserver(function(mutations) {
        // Проверяем, есть ли среди добавленных узлов что-то кроме статусных элементов
        const hasRelevantChanges = mutations.some(function(mutation) {
            if (!mutation.addedNodes || mutation.addedNodes.length === 0) {
                return false;
            }
            // Игнорируем изменения в элементах статуса и уведомлений
            return Array.from(mutation.addedNodes).some(function(node) {
                if (node.nodeType !== 1) return false; // Только элементы
                const id = node.id || '';
                return id !== 'freecad-status-message' && id !== 'temp-notification';
            });
        });
        
        if (hasRelevantChanges) {
            updateFreeCadButtonsVisibility();
            initLastNavButtons();
        }
    });
    
    // Наблюдаем за изменениями в DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Wire-up навигационных кнопок если они уже в DOM
    initLastNavButtons();
}); 
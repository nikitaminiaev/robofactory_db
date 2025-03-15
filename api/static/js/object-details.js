function renderObjectDetails(data) {
    let detailsHtml = `<table>
        <tr><th>ID</th><td>${data.id}</td></tr>
        <tr><th>Name</th><td>${data.name}</td></tr>
        <tr><th>Author</th><td>${data.author}</td></tr>
        <tr><th>Description</th><td>${data.description}</td></tr>
        ${data.coordinates ? `<tr><th>Coordinates</th><td>${JSON.stringify(data.coordinates)}</td></tr>` : ''}
        ${data.role ? `<tr><th>Role</th><td>${data.role}</td></tr>` : ''}
        ${data.role_description ? `<tr><th>Role Description</th><td>${data.role_description}</td></tr>` : ''}
        ${data.created_ts ? `<tr><th>Created</th><td>${data.created_ts}</td></tr>` : ''}
        ${data.updated_ts ? `<tr><th>Updated</th><td>${data.updated_ts}</td></tr>` : ''}
    </table>`;

    if (data.bounding_contour) {
        detailsHtml += `
            <h2>Bounding Contour</h2>
            <table>
                <tr><th>Is Assembly</th><td>${data.bounding_contour.is_assembly}</td></tr>
                <tr><th>BREP Files</th><td>${data.bounding_contour.brep_files}</td></tr>
            </table>`;
    }

    if (data.children && data.children.length > 0) {
        detailsHtml += '<h2>Children</h2><ul>';
        data.children.forEach(child => {
            detailsHtml += `<li>
                <a href="/basic_object/${child}">${child}</a>
                <button class="load-freecad-btn" data-id="${child}">Load FreeCad</button>
            </li>`;
        });
        detailsHtml += '</ul>';
    }

    if (data.parents && data.parents.length > 0) {
        detailsHtml += '<h2>Parents</h2><ul>';
        data.parents.forEach(parent => {
            detailsHtml += `<li>
                <a href="/basic_object/${parent}">${parent}</a>
                <button class="load-freecad-btn" data-id="${parent}">Load FreeCad</button>
            </li>`;
        });
        detailsHtml += '</ul>';
    }

    return detailsHtml;
}

// Функция для загрузки объекта во FreeCad
function loadObjectToFreeCad(objectId) {
    fetch(`/api/basic_object/${objectId}/load_freecad`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при загрузке объекта во FreeCad');
        }
        return response.json();
    })
    .then(data => {
        let message = 'Объект успешно отправлен во FreeCad';
        
        // Добавляем информацию о статусе WebSocket-сервера
        if (data.socket_server_running) {
            message += '\nWebSocket-сервер запущен';
            if (data.message_sent) {
                message += '\nСообщение "hello" успешно отправлено';
            } else {
                message += '\nНе удалось отправить сообщение "hello"';
            }
        } else {
            message += '\nWebSocket-сервер не запущен';
        }
        
        alert(message);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при загрузке объекта во FreeCad');
    });
}
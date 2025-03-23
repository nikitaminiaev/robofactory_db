function renderObjectDetails(data) {
    // Глобальный кэш имен объектов
    if (!window.objectNamesCache) {
        window.objectNamesCache = {};
    }

    let detailsHtml = `<table>
        <tr><th>ID</th><td>${data.id} <button class="load-freecad-btn" data-id="${data.id}" style="display: none;">Load FreeCad</button></td></tr>
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
                <tr><th>BREP Files</th><td>${
                    data.bounding_contour.brep_files 
                    && (typeof data.bounding_contour.brep_files === 'object' 
                        && Object.keys(data.bounding_contour.brep_files).length > 0 
                        || typeof data.bounding_contour.brep_files === 'string' 
                        && data.bounding_contour.brep_files.trim() !== '') ? 'Файлы доступны' : 'Нет файлов'}</td></tr>
            </table>`;
    }

    // Функция для загрузки имен объектов по ID
    const loadObjectNames = async (ids) => {
        if (!ids || ids.length === 0) return {};
        
        // Фильтруем только те ID, которых нет в кэше
        const uncachedIds = ids.filter(id => !window.objectNamesCache[id]);
        
        if (uncachedIds.length === 0) {
            // Если все ID уже в кэше, возвращаем их из кэша
            return ids.reduce((result, id) => {
                result[id] = window.objectNamesCache[id];
                return result;
            }, {});
        }
        
        try {
            const response = await fetch('/api/basic_objects/names', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ids: uncachedIds }),
            });
            
            if (!response.ok) {
                console.error('Ошибка при загрузке имен объектов:', response.statusText);
                return {};
            }
            
            const newNames = await response.json();
            
            // Добавляем новые имена в кэш
            Object.entries(newNames).forEach(([id, name]) => {
                window.objectNamesCache[id] = name;
            });
            
            // Возвращаем все запрошенные имена (из кэша и новые)
            return ids.reduce((result, id) => {
                result[id] = window.objectNamesCache[id] || id;
                return result;
            }, {});
        } catch (error) {
            console.error('Ошибка при загрузке имен объектов:', error);
            return {};
        }
    };

    // Функция для отображения списка детей или родителей
    const renderRelatedObjects = (elementId, title, ids) => {
        if (!ids || ids.length === 0) return;
        
        // Создаем контейнер для списка
        detailsHtml += `<h2>${title}</h2><ul id="${elementId}">`;
        
        // Сначала отображаем элементы только с ID
        ids.forEach(id => {
            detailsHtml += `<li>
                <a href="/basic_object/${id}" id="related-${id}">${window.objectNamesCache[id] || id}</a>
                <button class="load-freecad-btn" data-id="${id}" style="display: none;">Load FreeCad</button>
            </li>`;
        });
        
        detailsHtml += '</ul>';
        
        // После отрисовки шаблона загружаем имена и обновляем DOM
        setTimeout(async () => {
            const names = await loadObjectNames(ids);
            ids.forEach(id => {
                const element = document.getElementById(`related-${id}`);
                if (element && names[id]) {
                    // Сохраняем текст как "имя (id)" и сохраняем ссылку
                    element.textContent = `${names[id]}`;
                }
            });
        }, 0);
    };

    // Отображаем детей и родителей
    if (data.children && data.children.length > 0) {
        renderRelatedObjects('childrenList', 'Children', data.children);
    }

    if (data.parents && data.parents.length > 0) {
        renderRelatedObjects('parentsList', 'Parents', data.parents);
    }

    return detailsHtml;
}

// Примечание: функция loadObjectToFreeCad перенесена в файл freecad-integration.js
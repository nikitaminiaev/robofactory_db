/**
 * Модуль для отрисовки иерархической таблицы объектов
 */

function renderModulesTable(modules) {
    if (!modules || modules.length === 0) {
        return '<div class="info-message">Объекты не найдены</div>';
    }

    let html = `
    <table class="modules-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Author</th>
                <th>Description</th>
                <th>Created</th>
                <th>Is Assembly</th>
                <th>BREP Files</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    `;

    modules.forEach(module => {
        html += createModuleRow(module, 0, 'main');
    });

    html += `
        </tbody>
    </table>
    `;

    return html;
}

function createModuleRow(module, level, type = 'main') {
    const hasChildren = module.children && module.children.length > 0;
    const indent = level * 30;
    
    // Форматирование даты
    const created = module.created_ts ? new Date(module.created_ts).toLocaleString() : '-';
    
    // Данные из bounding_contour
    const isAssembly = module.bounding_contour ? (module.bounding_contour.is_assembly ? 'Yes' : 'No') : '-';
    const hasBrep = module.bounding_contour && module.bounding_contour.brep_files && Object.keys(module.bounding_contour.brep_files).length > 0;
    const brepStatus = hasBrep ? 'Available' : 'None';

    const rowClass = `module-row ${type}-row`;
    const rowId = `row-${module.id}`;

    return `
        <tr id="${rowId}" class="${rowClass}" data-id="${module.id}" data-level="${level}">
            <td class="name-cell" style="padding-left: ${indent + 15}px">
                <div class="tree-node-wrapper">
                    ${level > 0 ? '<div class="tree-connector-v"></div><div class="tree-connector-h"></div>' : ''}
                    <div class="tree-expander">
                        ${hasChildren ? `<button class="tree-expand-btn" onclick="toggleChildren('${module.id}', ${level}, this)">▸</button>` : ''}
                    </div>
                    <div class="module-name-box">
                        <span class="module-name-text">${module.name}</span>
                    </div>
                </div>
            </td>
            <td>${module.author}</td>
            <td class="desc-col" title="${module.description || ''}">${module.description || '-'}</td>
            <td>${created}</td>
            <td>${isAssembly}</td>
            <td>${brepStatus}</td>
            <td class="actions-col">
                <button class="load-freecad-btn" data-id="${module.id}" style="display: none;">Load FreeCad</button>
                <a href="/basic_object/${module.id}" class="view-page-link">Go to Page</a>
            </td>
        </tr>
    `;
}

async function toggleChildren(moduleId, level, btn) {
    const row = document.getElementById(`row-${moduleId}`);
    const isExpanded = btn.classList.contains('expanded');
    
    if (isExpanded) {
        // Сворачиваем - удаляем все дочерние строки, которые глубже текущего уровня
        let nextRow = row.nextElementSibling;
        while (nextRow && nextRow.classList.contains('child-row') && parseInt(nextRow.getAttribute('data-level')) > level) {
            let toRemove = nextRow;
            nextRow = nextRow.nextElementSibling;
            toRemove.remove();
        }
        btn.classList.remove('expanded');
        btn.textContent = '▸';
        return;
    }

    // Разворачиваем
    try {
        const response = await fetch(`/api/basic_objects/${moduleId}/children`);
        if (!response.ok) throw new Error('Failed to fetch children');
        
        const data = await response.json();
        const children = data.basic_objects;
        
        let lastRow = row;
        children.forEach(child => {
            const childRowHtml = createModuleRow(child, level + 1, 'child');
            lastRow.insertAdjacentHTML('afterend', childRowHtml);
            lastRow = document.getElementById(`row-${child.id}`);
        });
        
        btn.classList.add('expanded');
        btn.textContent = '▾';
        
        // Инициализируем новые кнопки FreeCad
        if (typeof updateFreeCadButtonsVisibility === 'function') {
            updateFreeCadButtonsVisibility();
        }
    } catch (error) {
        console.error('Error loading children:', error);
    }
}

// Удаляем функцию toggleParents так как она больше не нужна
// async function toggleParents(moduleId, level, btn) { ... }

// Новая функция для детального отображения объекта
function renderObjectFullDetails(data) {
    // Глобальный кэш имен объектов
    if (!window.objectNamesCache) {
        window.objectNamesCache = {};
    }

    let detailsHtml = `<div class="detail-view">
        <table class="detail-table">
            <tr><th>ID</th><td>${data.id} <button class="load-freecad-btn" data-id="${data.id}" style="display: none;">Load FreeCad</button></td></tr>
            <tr><th>Name</th><td>${data.name}</td></tr>
            <tr><th>Author</th><td>${data.author}</td></tr>
            <tr><th>Description</th><td>${data.description || '-'}</td></tr>
            ${data.coordinates ? `<tr><th>Coordinates</th><td>${JSON.stringify(data.coordinates)}</td></tr>` : ''}
            ${data.role ? `<tr><th>Role</th><td>${data.role}</td></tr>` : ''}
            ${data.role_description ? `<tr><th>Role Description</th><td>${data.role_description}</td></tr>` : ''}
            <tr><th>Created</th><td>${data.created_ts ? new Date(data.created_ts).toLocaleString() : '-'}</td></tr>
            <tr><th>Updated</th><td>${data.updated_ts ? new Date(data.updated_ts).toLocaleString() : '-'}</td></tr>
        </table>`;

    if (data.bounding_contour) {
        detailsHtml += `
            <h2>Bounding Contour</h2>
            <table class="detail-table">
                <tr><th>Is Assembly</th><td>${data.bounding_contour.is_assembly ? 'Yes' : 'No'}</td></tr>
                <tr><th>BREP Files</th><td>${
                    data.bounding_contour.brep_files 
                    && (typeof data.bounding_contour.brep_files === 'object' 
                        && Object.keys(data.bounding_contour.brep_files).length > 0 
                        || typeof data.bounding_contour.brep_files === 'string' 
                        && data.bounding_contour.brep_files.trim() !== '') ? 'Available' : 'None'}</td></tr>
            </table>`;
    }

    // Функция для загрузки имен объектов по ID
    const loadObjectNames = async (ids) => {
        if (!ids || ids.length === 0) return {};
        const uncachedIds = ids.filter(id => !window.objectNamesCache[id]);
        if (uncachedIds.length === 0) {
            return ids.reduce((result, id) => {
                result[id] = window.objectNamesCache[id];
                return result;
            }, {});
        }
        try {
            const response = await fetch('/api/basic_objects/names', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: uncachedIds }),
            });
            if (!response.ok) return {};
            const newNames = await response.json();
            Object.entries(newNames).forEach(([id, name]) => { window.objectNamesCache[id] = name; });
            return ids.reduce((result, id) => {
                result[id] = window.objectNamesCache[id] || id;
                return result;
            }, {});
        } catch (error) {
            console.error('Error loading names:', error);
            return {};
        }
    };

    const renderRelatedObjectsList = (title, ids, listId) => {
        if (!ids || ids.length === 0) return '';
        let listHtml = `<h2>${title}</h2><ul id="${listId}" class="related-list">`;
        ids.forEach(id => {
            listHtml += `<li>
                <a href="/basic_object/${id}" id="related-${listId}-${id}">${window.objectNamesCache[id] || id}</a>
                <button class="load-freecad-btn" data-id="${id}" style="display: none;">Load FreeCad</button>
            </li>`;
        });
        listHtml += '</ul>';

        setTimeout(async () => {
            const names = await loadObjectNames(ids);
            ids.forEach(id => {
                const element = document.getElementById(`related-${listId}-${id}`);
                if (element && names[id]) element.textContent = names[id];
            });
        }, 0);
        return listHtml;
    };

    detailsHtml += renderRelatedObjectsList('Parents', data.parents, 'parentsList');
    detailsHtml += renderRelatedObjectsList('Children', data.children, 'childrenList');
    detailsHtml += `</div>`;

    return detailsHtml;
}

// Сохраняем обратную совместимость, если где-то используется старая функция
function renderObjectDetails(data) {
    if (Array.isArray(data)) {
        return renderModulesTable(data);
    }
    // Если это не массив, значит мы на детальной странице
    return renderObjectFullDetails(data);
}

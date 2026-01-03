/**
 * Модуль для отрисовки иерархической таблицы объектов
 */

// Глобальное состояние сортировки
let currentSort = {
    column: null,
    direction: 'asc'
};

function renderModulesTable(modules, sortCol = null, sortDir = 'asc') {
    if (!modules || modules.length === 0) {
        return '<div class="info-message">Объекты не найдены</div>';
    }

    // Сохраняем данные для возможности повторной сортировки
    window.lastTableData = modules;
    currentSort.column = sortCol;
    currentSort.direction = sortDir;

    // Сортировка если указана колонка
    if (sortCol) {
        modules.sort((a, b) => {
            let valA, valB;
            
            switch(sortCol) {
                case 'name': valA = a.name; valB = b.name; break;
                case 'author': valA = a.author; valB = b.author; break;
                case 'created': valA = a.created_ts; valB = b.created_ts; break;
                case 'assembly': 
                    valA = a.bounding_contour ? (a.bounding_contour.is_assembly ? 1 : 0) : -1;
                    valB = b.bounding_contour ? (b.bounding_contour.is_assembly ? 1 : 0) : -1;
                    break;
                default: return 0;
            }

            if (valA < valB) return sortDir === 'asc' ? -1 : 1;
            if (valA > valB) return sortDir === 'asc' ? 1 : -1;
            return 0;
        });
    }

    const getSortIcon = (col) => {
        if (currentSort.column !== col) return '<span class="sort-icon">↕</span>';
        return currentSort.direction === 'asc' ? '<span class="sort-icon">↑</span>' : '<span class="sort-icon">↓</span>';
    };

    let html = `
    <div class="table-container">
        <table class="modules-table resizable-table">
            <thead>
                <tr>
                    <th style="width: 250px" class="sortable" onclick="handleSort('name')">Name ${getSortIcon('name')}<div class="resizer"></div></th>
                    <th style="width: 120px" class="sortable" onclick="handleSort('author')">Author ${getSortIcon('author')}<div class="resizer"></div></th>
                    <th style="width: 200px">Description<div class="resizer"></div></th>
                    <th style="width: 150px" class="sortable" onclick="handleSort('created')">Created ${getSortIcon('created')}<div class="resizer"></div></th>
                    <th style="width: 100px" class="sortable" onclick="handleSort('assembly')">Is Assembly ${getSortIcon('assembly')}<div class="resizer"></div></th>
                    <th style="width: 100px">BREP Files<div class="resizer"></div></th>
                    <th style="width: 180px">Actions<div class="resizer"></div></th>
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
    </div>
    `;

    // Инициализируем изменение ширины после вставки в DOM
    setTimeout(initResizableColumns, 0);

    return html;
}

function handleSort(column) {
    const direction = (currentSort.column === column && currentSort.direction === 'asc') ? 'desc' : 'asc';
    const sortedHtml = renderModulesTable(window.lastTableData, column, direction);
    
    // Находим контейнер и обновляем его содержимое
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        resultDiv.innerHTML = '<h2>Search Results:</h2>' + sortedHtml;
    } else {
        // Если мы не на странице поиска, возможно мы на другой странице с таблицей
        const tableContainer = document.querySelector('.table-container');
        if (tableContainer) {
            tableContainer.outerHTML = sortedHtml;
        }
    }
    
    // Обновляем видимость кнопок FreeCad
    if (typeof updateFreeCadButtonsVisibility === 'function') {
        updateFreeCadButtonsVisibility();
    }
}

function initResizableColumns() {
    const tables = document.querySelectorAll('.resizable-table');
    tables.forEach(table => {
        const headerRow = table.querySelector('thead tr');
        const cols = headerRow.querySelectorAll('th');
        
        // Устанавливаем начальную общую ширину таблицы в пикселях
        let tableWidth = 0;
        cols.forEach(col => {
            tableWidth += col.offsetWidth;
        });
        table.style.width = tableWidth + 'px';
        table.style.minWidth = tableWidth + 'px';

        cols.forEach(col => {
            const resizer = col.querySelector('.resizer');
            if (!resizer || resizer.dataset.initialized) return;
            
            resizer.dataset.initialized = "true";
            
            resizer.addEventListener('mousedown', function(e) {
                const startX = e.pageX;
                const startWidth = col.offsetWidth;
                const initialTableWidth = table.offsetWidth;
                
                resizer.classList.add('resizing');
                
                const onMouseMove = (e) => {
                    const delta = e.pageX - startX;
                    const newWidth = Math.max(50, startWidth + delta); // Минимум 50px
                    const actualDelta = newWidth - startWidth;
                    
                    col.style.width = newWidth + 'px';
                    
                    // Расширяем саму таблицу на величину изменения столбца
                    const newTableWidth = initialTableWidth + actualDelta;
                    table.style.width = newTableWidth + 'px';
                    table.style.minWidth = newTableWidth + 'px';
                };
                
                const onMouseUp = () => {
                    resizer.classList.remove('resizing');
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    document.body.style.cursor = 'default';
                };
                
                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
                document.body.style.cursor = 'col-resize';
                e.preventDefault();
            });
        });
    });
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
                    <a href="/basic_object/${module.id}" class="module-name-link">
                        <div class="module-name-box">
                            <span class="module-name-text">${module.name}</span>
                        </div>
                    </a>
                </div>
            </td>
            <td>${module.author}</td>
            <td class="desc-col" title="${module.description || ''}">${module.description || '-'}</td>
            <td>${created}</td>
            <td>${isAssembly}</td>
            <td>${brepStatus}</td>
            <td class="actions-col">
                <button class="load-freecad-btn" data-id="${module.id}" style="display: none;">Load FreeCad</button>
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
    // Сохраняем данные объекта для редактирования
    window.currentObjectData = data;
    
    // Глобальный кэш имен объектов
    if (!window.objectNamesCache) {
        window.objectNamesCache = {};
    }

    let detailsHtml = `<div class="detail-view" id="object-detail-container">
        <div class="action-buttons">
            <button id="edit-btn" onclick="toggleEditMode()">Edit</button>
            <button id="save-btn" class="save-btn" style="display: none;" onclick="saveObjectChanges()">Save</button>
            <button id="cancel-btn" class="cancel-btn" style="display: none;" onclick="toggleEditMode(false)">Cancel</button>
        </div>
        <table class="detail-table">
            <tr><th>ID</th><td>${data.id} <button class="load-freecad-btn" data-id="${data.id}" style="display: none;">Load FreeCad</button></td></tr>
            <tr><th>Name</th><td id="field-name">${data.name}</td></tr>
            <tr><th>Author</th><td id="field-author">${data.author}</td></tr>
            <tr><th>Description</th><td id="field-description">${data.description || '-'}</td></tr>
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
                <tr><th>Is Assembly</th><td id="field-is_assembly">${data.bounding_contour.is_assembly ? 'Yes' : 'No'}</td></tr>
                <tr><th>Is Shell</th><td id="field-is_shell">${data.bounding_contour.is_shell ? 'Yes' : 'No'}</td></tr>
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

function toggleEditMode(enable = true) {
    const container = document.getElementById('object-detail-container');
    const data = window.currentObjectData;
    
    if (enable) {
        container.classList.add('edit-mode');
        document.getElementById('edit-btn').style.display = 'none';
        document.getElementById('save-btn').style.display = 'inline-block';
        document.getElementById('cancel-btn').style.display = 'inline-block';
        
        // Превращаем поля в инпуты
        document.getElementById('field-name').innerHTML = `<input type="text" id="input-name" value="${data.name}">`;
        document.getElementById('field-author').innerHTML = `<input type="text" id="input-author" value="${data.author}">`;
        document.getElementById('field-description').innerHTML = `<textarea id="input-description">${data.description || ''}</textarea>`;
        
        if (data.bounding_contour) {
            document.getElementById('field-is_assembly').innerHTML = `<input type="checkbox" id="input-is_assembly" ${data.bounding_contour.is_assembly ? 'checked' : ''}>`;
            document.getElementById('field-is_shell').innerHTML = `<input type="checkbox" id="input-is_shell" ${data.bounding_contour.is_shell ? 'checked' : ''}>`;
        }
        
        // Добавляем возможность удаления родителей
        const parentsList = document.getElementById('parentsList');
        if (parentsList) {
            const parents = parentsList.querySelectorAll('li');
            parents.forEach(li => {
                if (!li.querySelector('.remove-btn')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn';
                    removeBtn.textContent = 'Remove';
                    removeBtn.onclick = () => {
                        li.style.display = 'none';
                        li.dataset.removed = 'true';
                    };
                    li.appendChild(removeBtn);
                }
            });
            
            // Добавляем секцию добавления родителя
            if (!document.getElementById('add-parent-section')) {
                const addParentSection = document.createElement('div');
                addParentSection.id = 'add-parent-section';
                addParentSection.className = 'add-child-section';
                addParentSection.innerHTML = `
                    <h3>Add Parent</h3>
                    <div class="add-child-grid">
                        <div style="position: relative;">
                            <input type="text" id="search-parent-input" placeholder="Search module by name..." oninput="searchModulesForRelation(this.value, 'parent')">
                            <div id="parent-search-results" class="search-results-dropdown" style="display: none;"></div>
                        </div>
                        <button onclick="addNewRelationToList('parent')">Add</button>
                    </div>
                `;
                parentsList.after(addParentSection);
            }
        } else {
            // Если списка родителей нет, создаем его для добавления новых
            const title = document.createElement('h2');
            title.textContent = 'Parents';
            const newList = document.createElement('ul');
            newList.id = 'parentsList';
            newList.className = 'related-list';
            
            const addParentSection = document.createElement('div');
            addParentSection.id = 'add-parent-section';
            addParentSection.className = 'add-child-section';
            addParentSection.innerHTML = `
                <h3>Add Parent</h3>
                <div class="add-child-grid">
                    <div style="position: relative;">
                        <input type="text" id="search-parent-input" placeholder="Search module by name..." oninput="searchModulesForRelation(this.value, 'parent')">
                        <div id="parent-search-results" class="search-results-dropdown" style="display: none;"></div>
                    </div>
                    <button onclick="addNewRelationToList('parent')">Add</button>
                </div>
            `;
            container.appendChild(title);
            container.appendChild(newList);
            container.appendChild(addParentSection);
        }

        // Добавляем возможность удаления детей
        const childrenList = document.getElementById('childrenList');
        if (childrenList) {
            const children = childrenList.querySelectorAll('li');
            children.forEach(li => {
                if (!li.querySelector('.remove-btn')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn';
                    removeBtn.textContent = 'Remove';
                    removeBtn.onclick = () => {
                        li.style.display = 'none';
                        li.dataset.removed = 'true';
                    };
                    li.appendChild(removeBtn);
                }
            });
            
            // Добавляем секцию добавления ребенка
            if (!document.getElementById('add-child-section')) {
                const addChildSection = document.createElement('div');
                addChildSection.id = 'add-child-section';
                addChildSection.className = 'add-child-section';
                addChildSection.innerHTML = `
                    <h3>Add Child</h3>
                    <div class="add-child-grid">
                        <div style="position: relative;">
                            <input type="text" id="search-child-input" placeholder="Search module by name..." oninput="searchModulesForRelation(this.value, 'child')">
                            <div id="child-search-results" class="search-results-dropdown" style="display: none;"></div>
                        </div>
                        <button onclick="addNewRelationToList('child')">Add</button>
                    </div>
                `;
                childrenList.after(addChildSection);
            }
        } else {
            // Если списка детей нет, создаем его для добавления новых
            const title = document.createElement('h2');
            title.textContent = 'Children';
            const newList = document.createElement('ul');
            newList.id = 'childrenList';
            newList.className = 'related-list';
            
            const addChildSection = document.createElement('div');
            addChildSection.id = 'add-child-section';
            addChildSection.className = 'add-child-section';
            addChildSection.innerHTML = `
                <h3>Add Child</h3>
                <div class="add-child-grid">
                    <div style="position: relative;">
                        <input type="text" id="search-child-input" placeholder="Search module by name..." oninput="searchModulesForRelation(this.value, 'child')">
                        <div id="child-search-results" class="search-results-dropdown" style="display: none;"></div>
                    </div>
                    <button onclick="addNewRelationToList('child')">Add</button>
                </div>
            `;
            container.appendChild(title);
            container.appendChild(newList);
            container.appendChild(addChildSection);
        }
    } else {
        // Выходим из режима редактирования - просто перерисовываем все
        const detailDiv = document.getElementById('objectDetails');
        if (detailDiv) {
            detailDiv.innerHTML = renderObjectDetails(data);
        }
    }
}

let selectedRelId = null;
let selectedRelType = null;

async function searchModulesForRelation(query, type) {
    const resultsDiv = document.getElementById(`${type}-search-results`);
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/basic_object?name=${encodeURIComponent(query)}`);
        const modules = await response.json();
        
        if (modules.length === 0) {
            resultsDiv.innerHTML = '<div class="search-result-item">No results</div>';
        } else {
            resultsDiv.innerHTML = modules
                .filter(m => m.id !== window.currentObjectData.id) // Нельзя добавить самого себя
                .map(m => `<div class="search-result-item" onclick="selectRelationForAdd('${m.id}', '${m.name}', '${type}')">${m.name} (${m.id})</div>`)
                .join('');
        }
        resultsDiv.style.display = 'block';
    } catch (e) {
        console.error('Error searching modules:', e);
    }
}

function selectRelationForAdd(id, name, type) {
    selectedRelId = id;
    selectedRelType = type;
    document.getElementById(`search-${type}-input`).value = name;
    document.getElementById(`${type}-search-results`).style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Показываем с небольшой задержкой для анимации
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function addNewRelationToList(type) {
    if (!selectedRelId || selectedRelType !== type) {
        showToast('Please select a module from the search results', 'error');
        return;
    }
    
    const name = document.getElementById(`search-${type}-input`).value;
    const list = document.getElementById(`${type}sList`);
    
    const li = document.createElement('li');
    li.dataset.newRelation = 'true';
    li.dataset.id = selectedRelId;
    
    // Координаты по умолчанию (нулевые)
    const coords = { x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0 };
    li.dataset.coordinates = JSON.stringify(coords);
    
    li.innerHTML = `
        <a href="/basic_object/${selectedRelId}">${name}</a>
        <span style="font-size: 11px; color: #666; margin-left: 10px;">(New)</span>
        <button class="remove-btn" onclick="this.parentElement.remove()">Remove</button>
    `;
    
    list.appendChild(li);
    
    // Сброс полей
    selectedRelId = null;
    selectedRelType = null;
    document.getElementById(`search-${type}-input`).value = '';
}

async function saveObjectChanges() {
    const data = window.currentObjectData;
    const updatePayload = {
        name: document.getElementById('input-name').value,
        author: document.getElementById('input-author').value,
        description: document.getElementById('input-description').value,
        is_assembly: document.getElementById('input-is_assembly') ? document.getElementById('input-is_assembly').checked : undefined,
        is_shell: document.getElementById('input-is_shell') ? document.getElementById('input-is_shell').checked : undefined,
        added_children: [],
        removed_children: [],
        added_parents: [],
        removed_parents: []
    };
    
    // Собираем изменения по родителям
    const parentsList = document.getElementById('parentsList');
    if (parentsList) {
        const parentItems = parentsList.querySelectorAll('li');
        parentItems.forEach(li => {
            if (li.dataset.removed === 'true') {
                const id = li.querySelector('a').href.split('/').pop();
                updatePayload.removed_parents.push(id);
            } else if (li.dataset.newRelation === 'true') {
                updatePayload.added_parents.push({
                    id: li.dataset.id,
                    coordinates: JSON.parse(li.dataset.coordinates)
                });
            }
        });
    }

    // Собираем изменения по детям
    const childrenList = document.getElementById('childrenList');
    if (childrenList) {
        const childItems = childrenList.querySelectorAll('li');
        childItems.forEach(li => {
            if (li.dataset.removed === 'true') {
                const id = li.querySelector('a').href.split('/').pop();
                updatePayload.removed_children.push(id);
            } else if (li.dataset.newRelation === 'true') {
                updatePayload.added_children.push({
                    id: li.dataset.id,
                    coordinates: JSON.parse(li.dataset.coordinates)
                });
            }
        });
    }
    
    try {
        const response = await fetch(`/api/basic_object/${data.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatePayload)
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to save changes');
        }
        
        showToast('Changes saved successfully!', 'success');
        
        // Перезагружаем через секунду, чтобы пользователь успел увидеть уведомление
        setTimeout(() => window.location.reload(), 1000);
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

// Сохраняем обратную совместимость, если где-то используется старая функция
function renderObjectDetails(data) {
    if (Array.isArray(data)) {
        return renderModulesTable(data);
    }
    // Если это не массив, значит мы на детальной странице
    return renderObjectFullDetails(data);
}

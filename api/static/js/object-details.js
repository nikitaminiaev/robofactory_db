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

function createModuleRow(module, level, type = 'main', countInParent = 1) {
    const hasChildren = module.children && module.children.length > 0;
    const indent = level * 30;
    
    // Форматирование даты
    const created = module.created_ts ? new Date(module.created_ts).toLocaleString() : '-';
    
    // Данные из bounding_contour
    const isAssembly = module.bounding_contour ? (module.bounding_contour.is_assembly ? 'Yes' : 'No') : '-';
    const hasBrep = module.bounding_contour && module.bounding_contour.brep_files && Object.keys(module.bounding_contour.brep_files).length > 0;
    const brepStatus = hasBrep ? 'Available' : 'None';

    const countBadge = countInParent > 1
        ? `<span class="child-count-badge" title="Количество вхождений">&times;${countInParent}</span>`
        : '';

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
                    ${countBadge}
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
        const childrenCounts = data.children_counts || {};
        
        let lastRow = row;
        children.forEach(child => {
            const countInParent = childrenCounts[child.id] || 1;
            const childRowHtml = createModuleRow(child, level + 1, 'child', countInParent);
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
            <button id="copy-btn" onclick="showCopyModal()">Copy Module</button>
            <button id="delete-btn" class="danger-btn" onclick="showDeleteModal()">Delete Module</button>
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

    const versions = window.currentModuleVersions || [];
    if (versions.length > 0) {
        const versionRows = versions.map(v => {
            const date = v.created_ts ? new Date(v.created_ts).toLocaleString() : '-';
            const statusBadge = v.is_released
                ? '<span style="color:#27ae60;font-weight:600;">Released</span>'
                : '<span style="color:#888;">In progress</span>';
            const commit = v.commit_hash ? `<code style="font-size:11px;">${v.commit_hash.slice(0, 8)}</code>` : '-';
            return `<tr>
                <td><strong>${v.version_number}</strong></td>
                <td>${v.description || '-'}</td>
                <td>${commit}</td>
                <td>${statusBadge}</td>
                <td style="white-space:nowrap;">${date}</td>
            </tr>`;
        }).join('');
        detailsHtml += `
            <h2>Версии</h2>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>Версия</th>
                        <th>Описание</th>
                        <th>Коммит</th>
                        <th>Статус</th>
                        <th>Дата</th>
                    </tr>
                </thead>
                <tbody>${versionRows}</tbody>
            </table>`;
    }

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

    const renderRelatedObjectsList = (title, ids, listId, counts) => {
        if (!ids || ids.length === 0) return '';
        let listHtml = `<h2>${title}</h2><ul id="${listId}" class="related-list">`;
        ids.forEach(id => {
            const count = counts && counts[id] > 1 ? counts[id] : null;
            const countBadge = count ? ` <span class="child-count-badge" title="Количество вхождений">&times;${count}</span>` : '';
            listHtml += `<li>
                <a href="/basic_object/${id}" id="related-${listId}-${id}">${window.objectNamesCache[id] || id}</a>${countBadge}
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
    detailsHtml += renderRelatedObjectsList('Children', data.children, 'childrenList', data.children_counts);
    detailsHtml += `
        <div id="copy-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Copy Module</h3>
                <form id="copy-form">
                    <div class="form-group">
                        <label for="copy-new-author">New Author:</label>
                        <input type="text" id="copy-new-author" required>
                    </div>
                    <div class="form-group">
                        <label for="copy-version-number">Version Number:</label>
                        <input type="text" id="copy-version-number" required>
                    </div>
                    <div class="form-group">
                        <label for="copy-description">Description:</label>
                        <textarea id="copy-description" required></textarea>
                    </div>
                    <div class="modal-actions">
                        <button type="button" onclick="submitCopyModule()">Submit</button>
                        <button type="button" onclick="hideCopyModal()">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <div id="delete-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Delete Module</h3>
                <p>Are you sure you want to delete this module? This action cannot be undone.</p>
                <p>Note: Parent and child modules will not be deleted, only their associations will be removed.</p>
                <div class="modal-actions">
                    <button type="button" class="danger-btn" onclick="confirmDeleteModule()">Delete</button>
                    <button type="button" onclick="hideDeleteModal()">Cancel</button>
                </div>
            </div>
        </div>
    `;
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
    const listIdMap = { child: 'childrenList', parent: 'parentsList' };
    const list = document.getElementById(listIdMap[type]);
    
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

// Функции для копирования модуля
function showCopyModal() {
    const modal = document.getElementById('copy-modal');
    const currentData = window.currentObjectData;

    // Заполняем поля по умолчанию
    document.getElementById('copy-new-author').value = currentData.author || '';

    // Автозаполнение версии
    fetchLatestVersion(currentData.id);

    document.getElementById('copy-description').value = '';

    modal.style.display = 'flex';
}

function hideCopyModal() {
    document.getElementById('copy-modal').style.display = 'none';
}

function showDeleteModal() {
    document.getElementById('delete-modal').style.display = 'flex';
}

function hideDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDeleteModule() {
    const moduleId = window.currentObjectData.id;

    try {
        const response = await fetch(`/api/basic_object/${moduleId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }

        showToast('Module deleted successfully!', 'success');
        hideDeleteModal();

        // Redirect to home page after 1 second
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function fetchLatestVersion(moduleId) {
    try {
        const response = await fetch(`/api/modules/${moduleId}/versions/latest`);
        if (response.ok) {
            const data = await response.json();
            // Увеличиваем версию: если 1.0 -> 1.1, если 1.9 -> 2.0
            const currentVersion = data.version_number || '0.0';
            const newVersion = incrementVersion(currentVersion);
            document.getElementById('copy-version-number').value = newVersion;
        } else {
            document.getElementById('copy-version-number').value = '1.0';
        }
    } catch (error) {
        console.error('Error fetching latest version:', error);
        document.getElementById('copy-version-number').value = '1.0';
    }
}

function incrementVersion(version) {
    const parts = version.split('.');
    if (parts.length >= 2) {
        const major = parseInt(parts[0]) || 0;
        const minor = parseInt(parts[1]) || 0;
        return `${major}.${minor + 1}`;
    }
    return '1.0';
}

async function submitCopyModule() {
    const form = document.getElementById('copy-form');
    if (!form.checkValidity()) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    const versionNumber = document.getElementById('copy-version-number').value;
    if (!isValidVersion(versionNumber)) {
        showToast('Version number must be in format X.Y (e.g., 1.0)', 'error');
        return;
    }

    const payload = {
        new_author: document.getElementById('copy-new-author').value,
        version_number: versionNumber,
        description: document.getElementById('copy-description').value
    };

    const moduleId = window.currentObjectData.id;

    try {
        const response = await fetch(`/api/modules/${moduleId}/copy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Copy failed');
        }

        const newModule = await response.json();
        showToast('Module copied successfully!', 'success');
        hideCopyModal();

        // Переход на страницу нового модуля через 1 секунду
        setTimeout(() => {
            window.location.href = `/basic_object/${newModule.id}`;
        }, 1000);
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

function isValidVersion(version) {
    const regex = /^\d+\.\d+$/;
    return regex.test(version);
}

async function checkScadAndActivateCommit(moduleId) {
    const btn = document.getElementById('commit-btn');
    if (!btn) return;

    try {
        const response = await fetch(`/api/modules/${moduleId}/cad-agent/has-scad`);
        if (!response.ok) return;
        const data = await response.json();
        if (!data.has_scad) return;
        btn.disabled = false;
        btn.title = 'Зафиксировать изменения .scad файла в git';
    } catch (error) {
        console.error('Error checking scad files:', error);
    }
}

async function commitScadChanges() {
    const moduleId = window.currentObjectData && window.currentObjectData.id;
    if (!moduleId) return;

    const commitMessage = window.prompt('Сообщение коммита:');
    if (!commitMessage || !commitMessage.trim()) return;

    const btn = document.getElementById('commit-btn');
    btn.disabled = true;

    try {
        const addResponse = await fetch(`/api/modules/${moduleId}/cad-agent/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'git add .' }),
        });
        if (!addResponse.ok) {
            const err = await addResponse.json();
            throw new Error(err.detail || 'git add failed');
        }

        const commitResponse = await fetch(`/api/modules/${moduleId}/cad-agent/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: `git commit -m "${commitMessage.trim().replace(/"/g, '\\"')}"` }),
        });
        if (!commitResponse.ok) {
            const err = await commitResponse.json();
            throw new Error(err.detail || 'git commit failed');
        }

        showToast('Коммит создан успешно!', 'success');
    } catch (error) {
        showToast('Ошибка коммита: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

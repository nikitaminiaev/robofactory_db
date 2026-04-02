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
    // Используем btn.closest('tr') вместо getElementById, чтобы корректно работать
    // когда один и тот же модуль встречается в DOM несколько раз (под разными родителями).
    const row = btn.closest('tr');
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
            // Берём nextElementSibling, а не getElementById — иначе при одинаковых id
            // в DOM получим первое вхождение, а не только что вставленную строку.
            lastRow = lastRow.nextElementSibling;
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
            <button id="btn-last-supersystem" data-id="${data.id}">Last Supersystem</button>
            <button id="btn-last-subsystem"   data-id="${data.id}">Last Subsystem</button>
            <button id="save-btn" class="save-btn" style="display: none;" onclick="saveObjectChanges()">Save</button>
            <button id="cancel-btn" class="cancel-btn" style="display: none;" onclick="toggleEditMode(false)">Cancel</button>
            <span id="freecad-btn-separator" class="freecad-action-btn" style="display:none; margin: 0 4px; color:#ccc;">|</span>
            <button id="btn-fc-save-brep"     class="freecad-action-btn" data-id="${data.id}" style="display:none;">Save BREP</button>
            <button id="btn-fc-save-position" class="freecad-action-btn" data-id="${data.id}" style="display:none;">Save Position</button>
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
    {
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
                <td><button class="edit-version-btn" onclick="openEditVersionModal('${v.id}', '${v.version_number}', ${JSON.stringify(v.description || '')}, ${v.is_released})" title="Редактировать версию">✎</button></td>
            </tr>`;
        }).join('');
        const emptyRow = versions.length === 0
            ? `<tr><td colspan="6" style="color:#aaa;text-align:center;">Нет версий</td></tr>`
            : '';
        detailsHtml += `
            <div style="display:flex;align-items:center;gap:10px;">
                <h2 style="margin:0;">Версии</h2>
                <button onclick="openAddVersionModal()" title="Добавить версию" style="padding:2px 10px;font-size:18px;line-height:1;cursor:pointer;">+</button>
            </div>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>Версия</th>
                        <th>Описание</th>
                        <th>Коммит</th>
                        <th>Статус</th>
                        <th>Дата</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>${versionRows}${emptyRow}</tbody>
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

    const renderRelatedObjectsList = (title, ids, listId, counts, childDataList = []) => {
        if (!ids || ids.length === 0) return '';
        
        // Для Children используем таблицу с колонкой Depth
        if (title === 'Children' && childDataList && childDataList.length > 0) {
            console.log('Rendering Children table with', childDataList.length, 'items', childDataList);
            
            // Группируем children по child_id
            const groupedChildren = {};
            childDataList.forEach((childData, index) => {
                const childId = childData.child_id;
                if (!groupedChildren[childId]) {
                    groupedChildren[childId] = [];
                }
                groupedChildren[childId].push({...childData, originalIndex: index});
            });
            
            let tableHtml = `<h2>${title}</h2>
                <table class="children-table" id="${listId}" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr>
                            <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Name</th>
                            <th style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd; width: 80px;">Depth</th>
                        </tr>
                    </thead>
                    <tbody>`;
            
            // Рендерим свернутые строки с ×2, ×3 и т.д.
            // Храним данные всех children в глобальном массиве
            window.childrenDepthData = [];
            
            Object.keys(groupedChildren).forEach((childId, groupIndex) => {
                const group = groupedChildren[childId];
                const count = group.length;
                const childName = window.objectNamesCache[childId] || childId;
                const countBadge = count > 1 ? ` <span class="child-count-badge expand-badge" data-group="${groupIndex}" style="cursor:pointer;" title="Нажмите для раскрытия">&times;${count}</span>` : '';
                
                tableHtml += `<tr class="child-group-row" data-group-index="${groupIndex}" data-child-id="${childId}">
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">
                        <a href="/basic_object/${childId}" class="child-link" data-group="${groupIndex}">${childName}</a>${countBadge}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                        ${count === 1 ? `<input type="number" class="child-depth-input single-depth" 
                            data-child-id="${childId}" 
                            data-pcm-id="${group[0].parent_child_module_id || ''}"
                            data-group-index="${groupIndex}"
                            min="0" max="10" value="1" 
                            style="width: 50px; padding: 4px; text-align: center;">` : '<span style="color:#999;">-</span>'}
                    </td>
                </tr>`;
                
                // Сохраняем данные в глобальный массив
                group.forEach((childData) => {
                    window.childrenDepthData.push({
                        child_id: childData.child_id,
                        parent_child_module_id: childData.parent_child_module_id || null,
                        depth: 1
                    });
                });
                
                // Если > 1, добавляем развернутые строки для настройки
                if (count > 1) {
                    group.forEach((childData, subIndex) => {
                        const pcmId = childData.parent_child_module_id;
                        tableHtml += `<tr class="child-expanded-row" data-parent-group="${groupIndex}" data-child-id="${childId}" data-pcm-id="${pcmId || ''}" style="display: none;">
                            <td style="padding: 8px; border-bottom: 1px solid #eee; padding-left: 20px; color: #666;">
                                <span class="child-link-expanded" data-group="${groupIndex}" data-sub="${subIndex}">${childName}</span>
                            </td>
                            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                                <input type="number" class="child-depth-input expanded-depth" 
                                    data-child-id="${childId}" 
                                    data-pcm-id="${pcmId || ''}"
                                    data-group-index="${groupIndex}"
                                    data-sub-index="${subIndex}"
                                    min="0" max="10" value="1" 
                                    style="width: 50px; padding: 4px; text-align: center;">
                            </td>
                        </tr>`;
                    });
                }
            });
            
            tableHtml += '</tbody></table>';
            
            // Загружаем имена
            const childIds = Object.keys(groupedChildren);
            setTimeout(async () => {
                const names = await loadObjectNames(childIds);
                childIds.forEach((childId, idx) => {
                    document.querySelectorAll(`.child-link[data-group="${idx}"]`).forEach(el => {
                        if (el && names[childId]) el.textContent = names[childId];
                    });
                    document.querySelectorAll(`.child-link-expanded[data-group="${idx}"]`).forEach(el => {
                        if (el && names[childId]) el.textContent = names[childId];
                    });
                });
                // Инициализируем кнопки FreeCAD
                updateFreeCadButtonsVisibility();
                // Загружаем сохраненные depth из localStorage
                loadChildDepthsFromLocalStorage();
                
                // Обработчики для раскрытия по клику на ×N
                document.querySelectorAll('.expand-badge').forEach(badge => {
                    badge.addEventListener('click', function() {
                        const groupIndex = this.dataset.group;
                        const expandedRows = document.querySelectorAll(`.child-expanded-row[data-parent-group="${groupIndex}"]`);
                        const isVisible = expandedRows[0] && expandedRows[0].style.display !== 'none';
                        
                        expandedRows.forEach(row => {
                            row.style.display = isVisible ? 'none' : 'table-row';
                        });
                        
                        this.textContent = isVisible ? `×${groupedChildren[childIds[groupIndex]].length}` : `▼×${groupedChildren[childIds[groupIndex]].length}`;
                    });
                });
                
                // Обработчики изменения depth - обновляем глобальный массив
                document.querySelectorAll('.child-depth-input').forEach(input => {
                    input.addEventListener('input', function() {
                        const childId = this.dataset.childId;
                        const pcmId = this.dataset.pcmId || '';
                        const depth = parseInt(this.value) || 0;
                        // Находим и обновляем запись в глобальном массиве
                        if (window.childrenDepthData) {
                            window.childrenDepthData.forEach(item => {
                                if (item.child_id === childId && (item.parent_child_module_id || '') === pcmId) {
                                    item.depth = depth;
                                }
                            });
                        }
                    });
                });
            }, 0);
            
            return tableHtml;
        }
        
        // Для Parents или если нет childDataList - старый формат списка
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
    
    // Функция для сохранения depth в localStorage
    function saveChildDepthsToLocalStorage() {
        const currentId = window.currentObjectData?.id;
        if (!currentId) return;
        
        const depthSettings = {};
        document.querySelectorAll('.child-depth-input').forEach(input => {
            const childId = input.dataset.childId;
            const pcmId = input.dataset.pcmId || '';
            const depth = parseInt(input.value) || 1;
            
            const key = pcmId ? `${childId}:${pcmId}` : childId;
            depthSettings[key] = depth;
        });
        
        const storageKey = `child_depths_${currentId}`;
        localStorage.setItem(storageKey, JSON.stringify(depthSettings));
    }
    
    // Функция для загрузки depth из localStorage
    function loadChildDepthsFromLocalStorage() {
        const currentId = window.currentObjectData?.id;
        if (!currentId) return;
        
        const storageKey = `child_depths_${currentId}`;
        const stored = localStorage.getItem(storageKey);
        if (!stored) return;
        
        try {
            const depthSettings = JSON.parse(stored);
            document.querySelectorAll('.child-depth-input').forEach(input => {
                const childId = input.dataset.childId;
                const pcmId = input.dataset.pcmId || '';
                const key = pcmId ? `${childId}:${pcmId}` : childId;
                if (depthSettings[key] !== undefined) {
                    input.value = depthSettings[key];
                }
            });
        } catch (e) {
            console.error('Error loading child depths from localStorage:', e);
        }
    }
    
    // Функция для получения child_depths массива для API
    window.getChildDepthsForApi = function() {
        // Обновляем значения из видимых input'ов
        document.querySelectorAll('.child-depth-input').forEach(input => {
            const childId = input.dataset.childId;
            const pcmId = input.dataset.pcmId || '';
            const depth = parseInt(input.value) || 0;
            if (window.childrenDepthData) {
                window.childrenDepthData.forEach(item => {
                    if (item.child_id === childId && (item.parent_child_module_id || '') === pcmId) {
                        item.depth = depth;
                    }
                });
            }
        });
        console.log('getChildDepthsForApi result:', window.childrenDepthData || []);
        return window.childrenDepthData || [];
    }

    detailsHtml += renderRelatedObjectsList('Parents', data.parents, 'parentsList', data.parent_counts);
    detailsHtml += renderRelatedObjectsList('Children', data.children, 'childrenList', data.children_counts, data.children_with_coordinates || []);
    detailsHtml += renderRolesMatrix(data);
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
        <div id="add-version-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Новая версия</h3>
                <form id="add-version-form">
                    <div class="form-group">
                        <label for="add-version-number">Номер версии:</label>
                        <input type="text" id="add-version-number" placeholder="1.0" required>
                    </div>
                    <div class="form-group">
                        <label for="add-version-description">Описание:</label>
                        <textarea id="add-version-description" required></textarea>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="add-version-released">
                        <label for="add-version-released" style="margin:0;">Релизная версия</label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" onclick="submitAddVersion()">Создать</button>
                        <button type="button" onclick="hideAddVersionModal()">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
        <div id="edit-version-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Редактировать версию</h3>
                <input type="hidden" id="edit-version-id">
                <form id="edit-version-form">
                    <div class="form-group">
                        <label for="edit-version-number">Номер версии:</label>
                        <input type="text" id="edit-version-number" required>
                    </div>
                    <div class="form-group">
                        <label for="edit-version-description">Описание:</label>
                        <textarea id="edit-version-description" required></textarea>
                    </div>
                    <div class="form-group" style="display:flex;align-items:center;gap:8px;">
                        <input type="checkbox" id="edit-version-released">
                        <label for="edit-version-released" style="margin:0;">Релизная версия</label>
                    </div>
                    <div class="modal-actions">
                        <button type="button" onclick="submitEditVersion()">Сохранить</button>
                        <button type="button" onclick="hideEditVersionModal()">Отмена</button>
                    </div>
                </form>
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

        // Добавляем возможность удаления детей (теперь таблица вместо списка)
        const childrenTable = document.querySelector('.children-table');
        if (childrenTable) {
            // Добавляем кнопки Remove к строкам таблицы
            childrenTable.querySelectorAll('tr.child-group-row').forEach(row => {
                if (!row.querySelector('.remove-btn')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn';
                    removeBtn.textContent = 'Remove';
                    removeBtn.style.marginLeft = '8px';
                    removeBtn.style.fontSize = '11px';
                    removeBtn.onclick = () => {
                        // Скрываем строку и все её развернутые строки
                        const childId = row.dataset.childId;
                        row.style.display = 'none';
                        row.dataset.removed = 'true';
                        childrenTable.querySelectorAll(`.child-expanded-row[data-child-id="${childId}"]`).forEach(expRow => {
                            expRow.style.display = 'none';
                            expRow.dataset.removed = 'true';
                        });
                    };
                    const nameCell = row.querySelector('td:first-child');
                    nameCell.appendChild(removeBtn);
                }
            });
            
            // Добавляем кнопки Remove к развернутым строкам
            childrenTable.querySelectorAll('tr.child-expanded-row').forEach(row => {
                if (!row.querySelector('.remove-btn')) {
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn';
                    removeBtn.textContent = 'Remove';
                    removeBtn.style.marginLeft = '8px';
                    removeBtn.style.fontSize = '11px';
                    removeBtn.onclick = () => {
                        row.style.display = 'none';
                        row.dataset.removed = 'true';
                    };
                    const nameCell = row.querySelector('td:first-child');
                    nameCell.appendChild(removeBtn);
                }
            });
            
            // Добавляем секцию добавления ребенка после таблицы
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
                childrenTable.after(addChildSection);
            }
        } else {
            // Если таблицы детей нет, создаем секцию для добавления
            const title = document.createElement('h2');
            title.textContent = 'Children';
            
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
    
    // Координаты по умолчанию (нулевые)
    const coords = { x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0 };
    
    if (type === 'child') {
        // Для детей добавляем строку в таблицу
        const table = document.querySelector('.children-table');
        if (table) {
            const tbody = table.querySelector('tbody');
            const row = document.createElement('tr');
            row.dataset.newRelation = 'true';
            row.dataset.id = selectedRelId;
            row.dataset.coordinates = JSON.stringify(coords);
            row.className = 'child-group-row';
            row.innerHTML = `
                <td style="padding: 8px; border-bottom: 1px solid #eee;">
                    <a href="/basic_object/${selectedRelId}">${name}</a>
                    <span style="font-size: 11px; color: #666; margin-left: 10px;">(New)</span>
                    <button class="remove-btn" onclick="this.parentElement.parentElement.remove()" style="margin-left: 8px; font-size: 11px;">Remove</button>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                    <input type="number" class="child-depth-input single-depth" 
                        data-child-id="${selectedRelId}" 
                        data-pcm-id=""
                        min="0" max="10" value="1" 
                        style="width: 50px; padding: 4px; text-align: center;">
                </td>
            `;
            tbody.appendChild(row);
            
            // Добавляем в глобальный массив
            if (window.childrenDepthData) {
                window.childrenDepthData.push({
                    child_id: selectedRelId,
                    parent_child_module_id: null,
                    depth: 1
                });
            }
        }
    } else {
        // Для родителей - как раньше
        const list = document.getElementById('parentsList');
        if (list) {
            const li = document.createElement('li');
            li.dataset.newRelation = 'true';
            li.dataset.id = selectedRelId;
            li.dataset.coordinates = JSON.stringify(coords);
            li.innerHTML = `
                <a href="/basic_object/${selectedRelId}">${name}</a>
                <span style="font-size: 11px; color: #666; margin-left: 10px;">(New)</span>
                <button class="remove-btn" onclick="this.parentElement.remove()">Remove</button>
            `;
            list.appendChild(li);
        }
    }
    
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
        removed_child_relations: [],
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

    // Собираем изменения по детям (теперь таблица вместо списка)
    const childrenTable = document.querySelector('.children-table');
    const removedChildIds = new Set();
    
    if (childrenTable) {
        // Новые дети (добавленные через Add Child)
        childrenTable.querySelectorAll('tr[data-new-relation="true"]').forEach(row => {
            updatePayload.added_children.push({
                id: row.dataset.id,
                coordinates: JSON.parse(row.dataset.coordinates || '{}')
            });
        });
        
        // Удалённые конкретные вхождения (развернутые строки) - по parent_child_module_id
        childrenTable.querySelectorAll('tr.child-expanded-row[data-removed="true"]').forEach(row => {
            const pcmId = row.dataset.pcmId;
            if (pcmId) updatePayload.removed_child_relations.push(pcmId);
        });
        
        // Удалённые группы целиком (group rows) - по child_id
        childrenTable.querySelectorAll('tr.child-group-row[data-removed="true"]').forEach(row => {
            const childId = row.dataset.childId;
            if (childId) removedChildIds.add(childId);
        });
        
        updatePayload.removed_children = Array.from(removedChildIds);
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

async function openAddVersionModal() {
    const moduleId = window.currentObjectData && window.currentObjectData.id;
    if (!moduleId) return;

    document.getElementById('add-version-released').checked = false;
    document.getElementById('add-version-description').value = '';

    try {
        const response = await fetch(`/api/modules/${moduleId}/versions/latest`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('add-version-number').value = incrementVersion(data.version_number || '0.0');
        } else {
            document.getElementById('add-version-number').value = '1.0';
        }
    } catch {
        document.getElementById('add-version-number').value = '1.0';
    }

    document.getElementById('add-version-modal').style.display = 'flex';
}

function hideAddVersionModal() {
    document.getElementById('add-version-modal').style.display = 'none';
}

async function submitAddVersion() {
    const moduleId = window.currentObjectData && window.currentObjectData.id;
    if (!moduleId) return;

    const versionNumber = document.getElementById('add-version-number').value.trim();
    const description = document.getElementById('add-version-description').value.trim();
    const isReleased = document.getElementById('add-version-released').checked;

    if (!versionNumber || !description) {
        showToast('Заполните все обязательные поля', 'error');
        return;
    }
    if (!isValidVersion(versionNumber)) {
        showToast('Номер версии должен быть в формате X.Y (например, 1.0)', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/modules/${moduleId}/versions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version_number: versionNumber, description, make_git_commit: isReleased, is_released: isReleased }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Ошибка создания версии');
        }
        const newVersion = await response.json();
        window.currentModuleVersions = [...(window.currentModuleVersions || []), newVersion];
        hideAddVersionModal();
        showToast('Версия создана', 'success');
        await refreshObjectDetails();
    } catch (error) {
        showToast('Ошибка: ' + error.message, 'error');
    }
}

function openEditVersionModal(versionId, versionNumber, description, isReleased) {
    document.getElementById('edit-version-id').value = versionId;
    document.getElementById('edit-version-number').value = versionNumber;
    document.getElementById('edit-version-description').value = description;
    document.getElementById('edit-version-released').checked = isReleased;
    document.getElementById('edit-version-modal').style.display = 'flex';
}

function hideEditVersionModal() {
    document.getElementById('edit-version-modal').style.display = 'none';
}

async function submitEditVersion() {
    const moduleId = window.currentObjectData && window.currentObjectData.id;
    if (!moduleId) return;

    const versionId = document.getElementById('edit-version-id').value;
    const versionNumber = document.getElementById('edit-version-number').value.trim();
    const description = document.getElementById('edit-version-description').value.trim();
    const isReleased = document.getElementById('edit-version-released').checked;

    if (!versionNumber || !description) {
        showToast('Заполните все обязательные поля', 'error');
        return;
    }
    if (!isValidVersion(versionNumber)) {
        showToast('Номер версии должен быть в формате X.Y (например, 1.0)', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/modules/${moduleId}/versions/${versionId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ version_number: versionNumber, description, is_released: isReleased }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Ошибка обновления версии');
        }
        const updated = await response.json();
        window.currentModuleVersions = (window.currentModuleVersions || []).map(v =>
            v.id === updated.id ? updated : v
        );
        hideEditVersionModal();
        showToast('Версия обновлена', 'success');
        await refreshObjectDetails();
    } catch (error) {
        showToast('Ошибка: ' + error.message, 'error');
    }
}

async function refreshObjectDetails() {
    const moduleId = window.currentObjectData && window.currentObjectData.id;
    if (!moduleId) return;
    try {
        const [moduleRes, versionsRes] = await Promise.all([
            fetch(`/api/basic_object/${moduleId}`),
            fetch(`/api/modules/${moduleId}/versions`),
        ]);
        if (!moduleRes.ok) return;
        const data = await moduleRes.json();
        window.currentObjectData = data;
        window.currentModuleVersions = versionsRes.ok ? await versionsRes.json() : [];
        const container = document.getElementById('object-detail-container');
        if (container) container.innerHTML = renderObjectDetails(data);
    } catch (error) {
        console.error('Ошибка обновления данных:', error);
    }
}

// =====================================================================
// Матрица ролей
// =====================================================================

function renderRolesMatrix(data) {
    if (!data.children || data.children.length === 0) return '';

    window.rolesMatrixCollapsed = window.rolesMatrixCollapsed || new Set();
    const parentId = data.id;

    const addRoleFormHtml = `
        <div id="roles-matrix-add-form" class="roles-matrix__add-form" style="display:none;">
            <input type="text" id="roles-matrix-new-name" placeholder="Название роли" class="roles-matrix__input">
            <input type="text" id="roles-matrix-new-desc" placeholder="Описание (необязательно)" class="roles-matrix__input">
            <button class="roles-matrix__btn roles-matrix__btn--confirm" onclick="rolesMatrixAddColumn('${parentId}')">Добавить</button>
        </div>`;

    return `
        <div class="roles-matrix__section" id="roles-matrix-section">
            <div class="roles-matrix__header">
                <h2>Роли дочерних модулей</h2>
                <button class="roles-matrix__edit-btn" id="roles-matrix-edit-btn" onclick="rolesMatrixEnableEdit('${parentId}')">Edit</button>
                <button class="roles-matrix__edit-btn roles-matrix__edit-btn--done" id="roles-matrix-done-btn" onclick="rolesMatrixDisableEdit('${parentId}')" style="display:none;">Done</button>
            </div>
            <div id="roles-matrix-table-wrapper">
                ${buildRolesMatrixTable(data, false, parentId)}
            </div>
            ${addRoleFormHtml}
        </div>`;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function rolesMatrixEnableEdit(parentId) {
    const data = window.currentObjectData;
    document.getElementById('roles-matrix-edit-btn').style.display = 'none';
    document.getElementById('roles-matrix-done-btn').style.display = 'inline-block';

    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    wrapper.innerHTML = buildRolesMatrixTable(data, true, parentId);

    document.getElementById('roles-matrix-add-form').style.display = 'flex';
}

function rolesMatrixDisableEdit(parentId) {
    const data = window.currentObjectData;
    document.getElementById('roles-matrix-edit-btn').style.display = 'inline-block';
    document.getElementById('roles-matrix-done-btn').style.display = 'none';

    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    wrapper.innerHTML = buildRolesMatrixTable(data, false, parentId);

    document.getElementById('roles-matrix-add-form').style.display = 'none';
}

function buildRolesMatrixTable(data, editMode, parentId) {
    const roles = data.roles || [];
    const childrenRoles = data.children_roles || {};
    const collapsed = window.rolesMatrixCollapsed || new Set();

    const headerCells = roles.map(role => {
        const isCollapsed = collapsed.has(role.id);
        const collapseIcon = isCollapsed ? '›' : '‹';
        const collapseTitle = isCollapsed ? 'Развернуть' : 'Свернуть';
        const collapseBtn = `<button class="roles-matrix__collapse-btn" onclick="rolesMatrixToggleColumn('${role.id}')" title="${collapseTitle}">${collapseIcon}</button>`;
        const deleteBtn = editMode
            ? `<button class="roles-matrix__delete-role-btn roles-matrix__col-label" onclick="rolesMatrixDeleteColumn('${parentId}', '${role.id}', '${escapeHtml(role.name)}')" title="Удалить роль из модуля">×</button>`
            : '';
        const collapsedClass = isCollapsed ? ' roles-matrix__col--collapsed' : '';
        return `<th class="roles-matrix__th${collapsedClass}" data-role-col="${role.id}" title="${escapeHtml(role.description || '')}">
            <div class="roles-matrix__th-inner">
                ${collapseBtn}
                <span class="roles-matrix__col-label">${escapeHtml(role.name)}</span>
                ${deleteBtn}
            </div>
        </th>`;
    }).join('');

    const bodyRows = (data.children || []).map(childId => {
        const cells = roles.map(role => {
            const isCollapsed = collapsed.has(role.id);
            const checked = (childrenRoles[childId] || []).includes(role.id) ? 'checked' : '';
            const collapsedClass = isCollapsed ? ' roles-matrix__col--collapsed' : '';
            if (editMode) {
                return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}"><input type="checkbox" class="roles-matrix__checkbox" data-child-id="${childId}" data-role-id="${role.id}" ${checked} onchange="rolesMatrixToggleAssignment(this, '${childId}', '${role.id}')"></td>`;
            }
            return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}"><input type="checkbox" class="roles-matrix__checkbox" ${checked} disabled></td>`;
        }).join('');

        const name = window.objectNamesCache && window.objectNamesCache[childId] ? escapeHtml(window.objectNamesCache[childId]) : childId;
        return `<tr data-child-id="${childId}">
            <td class="roles-matrix__child-name"><a href="/basic_object/${childId}">${name}</a></td>
            ${cells}
            ${editMode ? '<td class="roles-matrix__th roles-matrix__th--add"></td>' : ''}
        </tr>`;
    }).join('');

    return `<table class="roles-matrix">
        <thead><tr>
            <th class="roles-matrix__th roles-matrix__th--child">Модуль</th>
            ${headerCells}
            ${editMode ? '<th class="roles-matrix__th roles-matrix__th--add"></th>' : ''}
        </tr></thead>
        <tbody>${bodyRows}</tbody>
    </table>`;
}

function rolesMatrixToggleColumn(roleId) {
    if (!window.rolesMatrixCollapsed) window.rolesMatrixCollapsed = new Set();

    if (window.rolesMatrixCollapsed.has(roleId)) {
        window.rolesMatrixCollapsed.delete(roleId);
    } else {
        window.rolesMatrixCollapsed.add(roleId);
    }

    const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
    const parentId = window.currentObjectData?.id;
    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    if (wrapper && parentId) {
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
    }
}

async function rolesMatrixToggleAssignment(checkbox, childId, roleId) {
    const method = checkbox.checked ? 'POST' : 'DELETE';
    const url = method === 'POST'
        ? `/api/modules/${childId}/roles`
        : `/api/modules/${childId}/roles/${roleId}`;

    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (method === 'POST') options.body = JSON.stringify({ role_id: roleId });

    try {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(await res.text());

        const childrenRoles = window.currentObjectData.children_roles || {};
        if (!childrenRoles[childId]) childrenRoles[childId] = [];
        if (checkbox.checked) {
            if (!childrenRoles[childId].includes(roleId)) childrenRoles[childId].push(roleId);
        } else {
            childrenRoles[childId] = childrenRoles[childId].filter(id => id !== roleId);
        }
        window.currentObjectData.children_roles = childrenRoles;
    } catch (err) {
        checkbox.checked = !checkbox.checked;
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function rolesMatrixAddColumn(parentId) {
    const nameInput = document.getElementById('roles-matrix-new-name');
    const descInput = document.getElementById('roles-matrix-new-desc');
    const name = nameInput.value.trim();
    if (!name) {
        showToast('Введите название роли', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/modules/${parentId}/roles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description: descInput.value.trim() || null }),
        });
        if (!res.ok) throw new Error(await res.text());
        const newRole = await res.json();

        if (!window.currentObjectData.roles) window.currentObjectData.roles = [];
        window.currentObjectData.roles.push(newRole);

        nameInput.value = '';
        descInput.value = '';

        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, true, parentId);
        showToast('Роль добавлена', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function rolesMatrixDeleteColumn(parentId, roleId, roleName) {
    if (!confirm(`Удалить роль "${roleName}" из модуля?`)) return;

    try {
        const res = await fetch(`/api/modules/${parentId}/roles/${roleId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());

        window.currentObjectData.roles = (window.currentObjectData.roles || []).filter(r => r.id !== roleId);

        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, true, parentId);
        showToast('Роль удалена', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

function rolesMatrixHideAddForm() {
    document.getElementById('roles-matrix-add-form').style.display = 'none';
    document.getElementById('roles-matrix-new-name').value = '';
    document.getElementById('roles-matrix-new-desc').value = '';
}

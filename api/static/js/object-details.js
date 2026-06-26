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
        <div class="module-tabs" id="module-detail-tabs">
            <button class="module-tab-btn active" type="button" data-module-tab="overview">Overview</button>
            <button class="module-tab-btn" type="button" data-module-tab="roles">Roles</button>
            <button class="module-tab-btn" type="button" data-module-tab="scad">SCAD & Chat</button>
            <button class="module-tab-btn" type="button" data-module-tab="interfaces">Interfaces</button>
        </div>
        <div class="module-tab-panel active" data-module-tab-panel="overview">
        <table class="detail-table">
            <tr><th>ID</th><td>${data.id} ${
                data.bounding_contour && data.bounding_contour.brep_files
                && (typeof data.bounding_contour.brep_files === 'object' && Object.keys(data.bounding_contour.brep_files).length > 0
                    || typeof data.bounding_contour.brep_files === 'string' && data.bounding_contour.brep_files.trim() !== '')
                ? `<button class="load-freecad-btn" data-id="${data.id}" style="display: none;">Load FreeCad</button>`
                : `<button class="create-cad-btn" data-id="${data.id}" data-name="${data.name}" style="display: none;">Create CAD</button>`
            }</td></tr>
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

    const renderBoolMark = (value) => {
        if (value) {
            return '<span title="True" style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#eaf8ee;color:#2e7d32;font-weight:700;">✓</span>';
        }
        return '<span title="False" style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border:1px solid #d6dbe5;border-radius:50%;background:#fff;color:transparent;">✓</span>';
    };

    if (data.bounding_contour) {
        detailsHtml += `
            <h2>Bounding Contour</h2>
            <table class="detail-table">
                <tr><th>Is Assembly</th><td id="field-is_assembly">${renderBoolMark(data.bounding_contour.is_assembly)}</td></tr>
                <tr><th>Is Shell</th><td id="field-is_shell">${renderBoolMark(data.bounding_contour.is_shell)}</td></tr>
                <tr><th>BREP Files</th><td>${
                    data.bounding_contour.brep_files 
                    && (typeof data.bounding_contour.brep_files === 'object' 
                        && Object.keys(data.bounding_contour.brep_files).length > 0 
                        || typeof data.bounding_contour.brep_files === 'string' 
                        && data.bounding_contour.brep_files.trim() !== '') ? 'Available' : 'None'}</td></tr>
            </table>`;
    }

    // Interface summary widget
    const ifaces = data.interfaces || [];
    const ifaceMappings = data.interface_mappings || [];
    const mandatoryCount = ifaces.filter(i => i.is_mandatory).length;
    const serviceCount = ifaces.filter(i => i.is_service).length;
    const mappedPortIds = new Set(ifaceMappings.map(m => m.role_port_id));
    const allRolePorts = getExternalInterfacePorts(data);
    const mappedCount = allRolePorts.filter(p => mappedPortIds.has(p.id)).length;
    detailsHtml += `
        <div style="margin-top:16px;">
            <h2>Interfaces <span style="font-size:13px;font-weight:400;color:#666;">(overview)</span></h2>
            <table class="detail-table">
                <tr><th>Total</th><td>${ifaces.length} interfaces (${mandatoryCount} mandatory, ${serviceCount} service)</td></tr>
                <tr><th>Port Coverage</th><td>${mappedCount}/${allRolePorts.length} role ports covered by interfaces</td></tr>
            </table>
        </div>`;

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
                            <th style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd; width: 140px;">Actions</th>
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
                
                const hasBrep = group[0] && group[0].has_brep;
                const actionBtn = hasBrep
                    ? `<button class="load-freecad-btn" data-id="${childId}" style="display:none;">Load FreeCad</button>`
                    : `<button class="create-cad-btn" data-id="${childId}" data-name="${childName}" style="display:none;">Create CAD</button>`;

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
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">${actionBtn}</td>
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
                        const hasBrepExpanded = childData.has_brep;
                        const actionBtnExpanded = hasBrepExpanded
                            ? `<button class="load-freecad-btn" data-id="${childId}" style="display:none;">Load FreeCad</button>`
                            : `<button class="create-cad-btn" data-id="${childId}" data-name="${childName}" style="display:none;">Create CAD</button>`;

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
                            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">${actionBtnExpanded}</td>
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
    detailsHtml += `</div>`;
    detailsHtml += renderRolesTab(data, loadObjectNames);
    detailsHtml += `<div class="module-tab-panel" data-module-tab-panel="scad">
        <div id="module-scad-tab-slot" style="display:grid; gap:16px;"></div>
    </div>`;
    detailsHtml += `<div class="module-tab-panel" data-module-tab-panel="interfaces">
        ${renderInterfacesTab(data)}
    </div>`;
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
        <div id="create-child-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Создать дочерний модуль</h3>
                <form id="create-child-form">
                    <div class="form-group">
                        <label for="create-child-name">Название модуля:</label>
                        <input type="text" id="create-child-name" required placeholder="Введите название">
                    </div>
                    <div class="form-group">
                        <label for="create-child-role">Роль (опционально):</label>
                        <select id="create-child-role" style="width: 100%; padding: 6px;">
                            <option value="">— без роли —</option>
                        </select>
                    </div>
                    <div class="modal-actions">
                        <button type="button" onclick="submitCreateChildModule()">Создать</button>
                        <button type="button" onclick="hideCreateChildModal()">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
        <div id="create-parent-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>Создать родительский модуль</h3>
                <form id="create-parent-form">
                    <div class="form-group">
                        <label for="create-parent-name">Название модуля:</label>
                        <input type="text" id="create-parent-name" required placeholder="Введите название">
                    </div>
                    <div class="modal-actions">
                        <button type="button" onclick="submitCreateParentModule()">Создать</button>
                        <button type="button" onclick="hideCreateParentModal()">Отмена</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    detailsHtml += `</div>`;

    return detailsHtml;
}

function renderExternalRolesTable(data, loadObjectNames) {
    const parentEdges = Array.isArray(data.parent_edges) ? data.parent_edges : [];
    if (parentEdges.length === 0) {
        return `
            <div class="section-card">
                <h2 style="margin-top:0;">External Roles</h2>
                <div class="info-message">No external roles found.</div>
            </div>
        `;
    }

    const parentIds = [...new Set(parentEdges.map(edge => edge.parent_id).filter(Boolean))];
    setTimeout(async () => {
        const names = await loadObjectNames(parentIds);
        parentIds.forEach(parentId => {
            const parentName = names[parentId];
            if (!parentName) return;
            document.querySelectorAll(`.external-role-parent-name[data-parent-id="${parentId}"]`).forEach(link => {
                link.textContent = parentName;
            });
        });
    }, 0);

    const rows = parentEdges.map(edge => `
        <tr>
            <td>
                <a
                    href="/basic_object/${edge.parent_id}"
                    class="external-role-parent-name"
                    data-parent-id="${edge.parent_id}"
                >${window.objectNamesCache[edge.parent_id] || edge.parent_id}</a>
            </td>
            <td>${edge.role_name ? renderRoleLink(edge.role_id, edge.role_name) : '—'}</td>
            <td>${edge.role_description ? escapeHtml(edge.role_description) : '—'}</td>
        </tr>
    `).join('');

    return `
        <div class="section-card">
            <h2 style="margin-top:0;">External Roles</h2>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>Parent module</th>
                        <th>Role</th>
                        <th>Role description</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderRolesTab(data, loadObjectNames) {
    const internalRolesHtml = renderRolesMatrix(data) || '<div class="info-message">This module has no child roles.</div>';
    const externalRolesHtml = renderExternalRolesTable(data, loadObjectNames);
    const externalStreamsHtml = renderExternalStreamsTable(data);
    const streamsHtml = renderStreamsMatrix(data);
    return `
        <div class="module-tab-panel" data-module-tab-panel="roles">
            ${internalRolesHtml}
            ${externalRolesHtml}
            ${streamsHtml}
            ${externalStreamsHtml}
            ${renderStreamModal()}
        </div>
    `;
}

function getInternalStreamRoles(data) {
    const roles = data.roles || [];
    const externalRoleIds = new Set(
        (data.parent_edges || [])
            .map(edge => edge.role_id)
            .filter(Boolean)
    );
    return roles.filter(role => !externalRoleIds.has(role.id));
}

function renderStreamsMatrix(data) {
    const roles = getInternalStreamRoles(data);
    if (roles.length < 2) {
        return `
            <div class="section-card" id="streams-matrix-section">
                <h2 style="margin-top:0;">Streams</h2>
                <div class="info-message">Add at least two roles to connect them with streams.</div>
            </div>
        `;
    }

    const roleIds = new Set(roles.map(role => role.id));
    const roleStreams = (data.role_streams || []).filter(stream => (
        roleIds.has(stream.source_role_id) &&
        roleIds.has(stream.target_role_id)
    ));
    const streamsByPair = new Map();
    roleStreams.forEach(stream => {
        const key = `${stream.source_role_id}:${stream.target_role_id}`;
        if (!streamsByPair.has(key)) streamsByPair.set(key, []);
        streamsByPair.get(key).push(stream);
    });
    const headerCells = roles.map(role => `
        <th class="streams-matrix__th" title="${escapeHtml(role.description || '')}">
            <span class="streams-matrix__target-label">→ ${renderRoleLink(role.id, role.name)}</span>
        </th>
    `).join('');

    const bodyRows = roles.map(sourceRole => {
        const cells = roles.map(targetRole => renderStreamMatrixCell(sourceRole, targetRole, streamsByPair));
        return `
            <tr>
                <th class="streams-matrix__role" title="${escapeHtml(sourceRole.description || '')}">
                    <span class="streams-matrix__source-label">${renderRoleLink(sourceRole.id, sourceRole.name)} →</span>
                </th>
                ${cells.join('')}
            </tr>
        `;
    }).join('');

    return `
        <div class="section-card" id="streams-matrix-section">
            <div class="streams-matrix__header">
                <h2>Streams</h2>
            </div>
            <div id="streams-matrix-wrapper" class="streams-matrix__wrapper">
                <table class="streams-matrix">
                    <thead>
                        <tr>
                            <th class="streams-matrix__corner">From ↓ / To →</th>
                            ${headerCells}
                        </tr>
                    </thead>
                    <tbody>${bodyRows}</tbody>
                </table>
            </div>
        </div>
    `;
}

function renderStreamMatrixCell(sourceRole, targetRole, streamsByPair) {
    if (sourceRole.id === targetRole.id) {
        return '<td class="streams-matrix__cell streams-matrix__cell--disabled">—</td>';
    }

    const streams = streamsByPair.get(`${sourceRole.id}:${targetRole.id}`) || [];
    const hasStreamClass = streams.length > 0 ? ' streams-matrix__cell-btn--filled' : '';
    const label = streams.length === 0
        ? '+'
        : streams.length === 1
            ? `→ ${escapeHtml(streams[0].name)}${renderStreamPortsSuffix(streams[0])}`
            : `→ ${streams.length} streams`;
    const title = streams.length > 0
        ? `Edit streams: ${streams.map(stream => `${stream.name}${formatStreamPortsText(stream)}`).join(', ')}`
        : 'Create stream';

    return `
        <td class="streams-matrix__cell">
            <button
                type="button"
                class="streams-matrix__cell-btn${hasStreamClass}"
                title="${title}"
                onclick="showStreamModal('${sourceRole.id}', '${targetRole.id}')"
            >${label}</button>
        </td>
    `;
}

function formatStreamPortsText(stream) {
    const sourcePort = stream.source_port_name || 'role';
    const targetPort = stream.target_port_name || 'role';
    if (!stream.source_port_name && !stream.target_port_name) return '';
    return ` (${sourcePort} → ${targetPort})`;
}

function renderStreamPortsSuffix(stream) {
    const text = formatStreamPortsText(stream);
    if (!text) return '';
    return `<small>${escapeHtml(text)}</small>`;
}

function renderExternalStreamsTable(data) {
    const externalStreams = data.external_role_streams || [];
    if (externalStreams.length === 0) {
        return `
            <div class="section-card">
                <h2 style="margin-top:0;">External Streams</h2>
                <div class="info-message">No external streams found.</div>
            </div>
        `;
    }

    const rows = externalStreams.map(stream => `
        <tr>
            <td>
                <a href="/basic_object/${stream.parent_module_id}">
                    ${escapeHtml(stream.parent_module_name || stream.parent_module_id)}
                </a>
            </td>
            <td>${renderRoleLink(stream.source_role_id, stream.source_role_name || stream.source_role_id)}</td>
            <td class="external-streams__direction">→</td>
            <td>${renderRoleLink(stream.target_role_id, stream.target_role_name || stream.target_role_id)}</td>
            <td>
                <strong>${escapeHtml(stream.name)}</strong>
                ${formatStreamPortsText(stream) ? `<small>${escapeHtml(formatStreamPortsText(stream))}</small>` : ''}
                ${stream.description ? `<small>${escapeHtml(stream.description)}</small>` : ''}
            </td>
        </tr>
    `).join('');

    return `
        <div class="section-card">
            <h2 style="margin-top:0;">External Streams</h2>
            <table class="detail-table external-streams">
                <thead>
                    <tr>
                        <th>Parent module</th>
                        <th>From role</th>
                        <th></th>
                        <th>To role</th>
                        <th>Stream</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderStreamModal() {
    return `
        <div id="stream-modal" class="modal" style="display: none;">
            <div class="modal-content modal-content--streams">
                <h3 id="stream-modal-title">Stream</h3>
                <input type="hidden" id="stream-source-role-id">
                <input type="hidden" id="stream-target-role-id">
                <div id="visual-stream-editor"></div>
                <div id="stream-existing-list" class="stream-existing-list"></div>
                <div style="display:none;">
                    <select id="stream-source-port"></select>
                    <select id="stream-target-port"></select>
                    <input type="text" id="stream-name">
                    <textarea id="stream-description"></textarea>
                    <input type="text" id="stream-search">
                    <div id="stream-search-results"></div>
                </div>
                <div class="modal-actions">
                    <button type="button" id="stream-delete-btn" class="danger-btn" onclick="deleteRoleStream()">Удалить все потоки</button>
                    <button type="button" onclick="saveRoleStream()" style="display:none;">Сохранить</button>
                    <button type="button" onclick="hideStreamModal()">Закрыть</button>
                </div>
            </div>
        </div>
    `;
}

function getRoleStreams(sourceRoleId, targetRoleId) {
    const roleStreams = window.currentObjectData?.role_streams || [];
    return roleStreams.filter(stream => (
        stream.source_role_id === sourceRoleId &&
        stream.target_role_id === targetRoleId
    ));
}

function getRoleById(roleId) {
    const roles = window.currentObjectData?.roles || [];
    return roles.find(role => role.id === roleId);
}

function getPortsByRoleId(roleId) {
    const role = getRoleById(roleId);
    return role?.ports || [];
}

function renderPortOptions(roleId, selectedPortId = null) {
    const options = ['<option value="">Вся роль без порта</option>'];
    getPortsByRoleId(roleId).forEach(port => {
        const selected = port.id === selectedPortId ? ' selected' : '';
        const direction = port.direction ? ` (${port.direction})` : '';
        options.push(`<option value="${port.id}"${selected}>${escapeHtml(port.name)}${escapeHtml(direction)}</option>`);
    });
    return options.join('');
}

function showStreamModal(sourceRoleId, targetRoleId) {
    const modal = document.getElementById('stream-modal');
    if (!modal) return;

    const streams = getRoleStreams(sourceRoleId, targetRoleId);
    const sourceRole = getRoleById(sourceRoleId);
    const targetRole = getRoleById(targetRoleId);
    const title = streams.length > 0 ? 'Редактировать streams' : 'Создать stream';

    document.getElementById('stream-modal-title').textContent =
        `${title}: ${sourceRole?.name || sourceRoleId} → ${targetRole?.name || targetRoleId}`;
    document.getElementById('stream-source-role-id').value = sourceRoleId;
    document.getElementById('stream-target-role-id').value = targetRoleId;
    document.getElementById('stream-name').value = '';
    document.getElementById('stream-description').value = '';
    document.getElementById('stream-source-port').innerHTML = renderPortOptions(sourceRoleId);
    document.getElementById('stream-target-port').innerHTML = renderPortOptions(targetRoleId);
    document.getElementById('stream-delete-btn').style.display = streams.length > 0 ? 'inline-block' : 'none';
    window.editingStreamId = null;
    window.selectedSourcePortId = null;

    if (resizeObserver) resizeObserver.disconnect();

    renderVisualStreamEditor(sourceRole, targetRole, streams);
    renderStreamExistingList(streams);
    resetStreamSearchSelection();

    modal.style.display = 'flex';
}

function renderStreamExistingList(streams) {
    const list = document.getElementById('stream-existing-list');
    if (!list) return;
    if (!streams || streams.length === 0) {
        list.innerHTML = '';
        return;
    }

    list.innerHTML = `
        <div class="stream-existing-list__title">Потоки в этой ячейке:</div>
        ${streams.map(stream => `
            <div class="stream-existing-list__item">
                <div>
                    <strong>${escapeHtml(stream.name)}</strong>
                    ${formatStreamPortsText(stream) ? `<small>${escapeHtml(formatStreamPortsText(stream))}</small>` : ''}
                    ${stream.description ? `<small>${escapeHtml(stream.description)}</small>` : ''}
                </div>
                <div class="stream-existing-list__actions">
                    <button type="button" class="stream-existing-list__edit" onclick="editRoleStream('${stream.id}', event)">✎</button>
                    <button type="button" class="stream-existing-list__delete" onclick="deleteSingleRoleStream('${stream.id}')">Удалить</button>
                </div>
            </div>
        `).join('')}
    `;
}

function editRoleStream(streamId, event) {
    const sourceRoleId = document.getElementById('stream-source-role-id').value;
    const targetRoleId = document.getElementById('stream-target-role-id').value;
    const streams = getRoleStreams(sourceRoleId, targetRoleId);
    const stream = streams.find(s => s.id === streamId);
    if (!stream) return;

    window.editingStreamId = streamId;
    document.getElementById('stream-name').value = stream.name;
    document.getElementById('stream-description').value = stream.description || '';
    document.getElementById('stream-source-port').innerHTML = renderPortOptions(sourceRoleId, stream.source_port_id);
    document.getElementById('stream-target-port').innerHTML = renderPortOptions(targetRoleId, stream.target_port_id);
    if (window.selectedExistingStream === null) {
        document.getElementById('stream-search').value = stream.name;
        window.selectedExistingStream = { name: stream.name, description: stream.description || '' };
    }

    const btnEl = event?.currentTarget || event?.target;
    if (btnEl) {
        const rect = btnEl.getBoundingClientRect();
        const containerEl = document.getElementById('viz-stream-popover');
        if (containerEl) {
            const parentRect = containerEl.parentElement.getBoundingClientRect();
            showStreamPopover(
                rect.left - parentRect.left + rect.width / 2,
                rect.top - parentRect.top - 10,
                'edit',
                stream
            );
        }
    }
}

function hideStreamModal() {
    const modal = document.getElementById('stream-modal');
    if (!modal) return;
    if (resizeObserver) resizeObserver.disconnect();
    window.editingStreamId = null;
    window.selectedSourcePortId = null;
    modal.style.display = 'none';
    document.getElementById('stream-name').value = '';
    document.getElementById('stream-description').value = '';
    resetStreamSearchSelection();
}

async function searchStreamsForModal(query) {
    const resultsDiv = document.getElementById('stream-search-results');
    if (!resultsDiv) return;

    window.selectedExistingStream = null;
    if (!query || query.trim().length < 1) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        return;
    }

    try {
        const res = await fetch(`/api/streams?query=${encodeURIComponent(query.trim())}&limit=20`);
        if (!res.ok) throw new Error(await res.text());
        const streams = await res.json();

        if (streams.length === 0) {
            resultsDiv.innerHTML = '<div class="stream-search-empty">Совпадений нет. Можно создать новый поток ниже.</div>';
        } else {
            resultsDiv.innerHTML = streams.map(stream => `
                <button
                    type="button"
                    class="stream-search-item"
                    onclick="selectStreamForModal(decodeURIComponent('${encodeURIComponent(stream.name)}'), decodeURIComponent('${encodeURIComponent(stream.description || '')}'))"
                >
                    <span>${escapeHtml(stream.name)}</span>
                    ${stream.description ? `<small>${escapeHtml(stream.description)}</small>` : ''}
                </button>
            `).join('');
        }
        resultsDiv.style.display = 'block';
    } catch (err) {
        resultsDiv.innerHTML = '<div class="stream-search-empty">Ошибка поиска потоков</div>';
        resultsDiv.style.display = 'block';
    }
}

function selectStreamForModal(name, description) {
    window.selectedExistingStream = { name, description };
    document.getElementById('stream-search').value = name;
    document.getElementById('stream-name').value = name;
    document.getElementById('stream-description').value = description || '';
    const resultsDiv = document.getElementById('stream-search-results');
    if (resultsDiv) resultsDiv.style.display = 'none';
}

function resetStreamSearchSelection() {
    window.selectedExistingStream = null;
    const searchInput = document.getElementById('stream-search');
    const resultsDiv = document.getElementById('stream-search-results');
    if (searchInput) searchInput.value = '';
    if (resultsDiv) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
    }
}

async function saveRoleStream(sourcePortOverride, targetPortOverride) {
    const moduleId = window.currentObjectData?.id;
    const sourceRoleId = document.getElementById('stream-source-role-id')?.value;
    const targetRoleId = document.getElementById('stream-target-role-id')?.value;
    const sourcePortId = sourcePortOverride ?? (document.getElementById('stream-source-port')?.value || null);
    const targetPortId = targetPortOverride ?? (document.getElementById('stream-target-port')?.value || null);
    const name = document.getElementById('stream-name')?.value.trim();
    const description = document.getElementById('stream-description')?.value.trim() || null;

    if (!moduleId || !sourceRoleId || !targetRoleId) {
        showToast('Ошибка: не найдены данные ячейки stream', 'error');
        return;
    }
    if (!name) {
        showToast('Введите название потока', 'error');
        return;
    }

    try {
        const body = {
            source_role_id: sourceRoleId,
            target_role_id: targetRoleId,
            source_port_id: sourcePortId,
            target_port_id: targetPortId,
            name,
            description,
        };
        if (window.editingStreamId) {
            body.stream_id = window.editingStreamId;
        }

        const res = await fetch(`/api/modules/${moduleId}/role-streams`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(await res.text());

        const savedStream = await res.json();
        upsertRoleStreamInCurrentData(savedStream);
        rerenderStreamsMatrix();
        hideStreamModal();
        showToast(window.editingStreamId ? 'Stream обновлён' : 'Stream добавлен', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function deleteRoleStream() {
    const moduleId = window.currentObjectData?.id;
    const sourceRoleId = document.getElementById('stream-source-role-id')?.value;
    const targetRoleId = document.getElementById('stream-target-role-id')?.value;

    if (!moduleId || !sourceRoleId || !targetRoleId) {
        showToast('Ошибка: не найдены данные ячейки stream', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/modules/${moduleId}/role-streams/${sourceRoleId}/${targetRoleId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(await res.text());

        removeRoleStreamFromCurrentData(sourceRoleId, targetRoleId);
        rerenderStreamsMatrix();
        hideStreamModal();
        showToast('Stream удален из ячейки', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function deleteSingleRoleStream(streamId) {
    const moduleId = window.currentObjectData?.id;
    const sourceRoleId = document.getElementById('stream-source-role-id')?.value;
    const targetRoleId = document.getElementById('stream-target-role-id')?.value;

    if (!moduleId || !sourceRoleId || !targetRoleId || !streamId) {
        showToast('Ошибка: не найдены данные stream', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/modules/${moduleId}/role-streams/${sourceRoleId}/${targetRoleId}/${streamId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(await res.text());

        removeRoleStreamFromCurrentData(sourceRoleId, targetRoleId, streamId);
        rerenderStreamsMatrix();
        const streams = getRoleStreams(sourceRoleId, targetRoleId);
        renderStreamExistingList(streams);
        drawStreamLines(streams);
        hideStreamPopover();
        document.getElementById('stream-delete-btn').style.display = streams.length > 0 ? 'inline-block' : 'none';
        showToast('Stream удален из ячейки', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

function upsertRoleStreamInCurrentData(savedStream) {
    const roleStreams = window.currentObjectData.role_streams || [];
    const nextStreams = roleStreams.filter(stream => (
        stream.source_role_id !== savedStream.source_role_id ||
        stream.target_role_id !== savedStream.target_role_id ||
        stream.id !== savedStream.id
    ));
    nextStreams.push(savedStream);
    window.currentObjectData.role_streams = nextStreams;
}

function removeRoleStreamFromCurrentData(sourceRoleId, targetRoleId, streamId = null) {
    const roleStreams = window.currentObjectData.role_streams || [];
    window.currentObjectData.role_streams = roleStreams.filter(stream => (
        stream.source_role_id !== sourceRoleId ||
        stream.target_role_id !== targetRoleId ||
        (streamId && stream.id !== streamId)
    ));
}

function rerenderStreamsMatrix() {
    const section = document.getElementById('streams-matrix-section');
    if (!section || !window.currentObjectData) return;
    section.outerHTML = renderStreamsMatrix(window.currentObjectData);
}

// ===== Visual Stream Editor =====

function renderVisualStreamEditor(sourceRole, targetRole, streams) {
    const container = document.getElementById('visual-stream-editor');
    if (!container) return;

    container.innerHTML = `
        <div class="viz-stream-container" id="viz-stream-container">
            <div class="viz-role-block viz-role-block--source" data-role-id="${sourceRole.id}">
                <div class="viz-role-block__header">${escapeHtml(sourceRole.name)}</div>
                <div class="viz-role-block__ports">
                    ${renderPortsForEditor(sourceRole, 'source')}
                </div>
            </div>
            <div class="viz-stream-canvas" id="viz-stream-canvas">
                <svg width="100%" height="100%" style="display:block;">
                    <defs>
                        <marker id="viz-arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#27ae60" />
                        </marker>
                        <marker id="viz-arrowhead-selected" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#e67e22" />
                        </marker>
                    </defs>
                    <g id="viz-stream-lines" style="pointer-events:auto;"></g>
                    <g id="viz-temp-line" style="pointer-events:none;"></g>
                </svg>
            </div>
            <div class="viz-role-block viz-role-block--target" data-role-id="${targetRole.id}">
                <div class="viz-role-block__header">${escapeHtml(targetRole.name)}</div>
                <div class="viz-role-block__ports">
                    ${renderPortsForEditor(targetRole, 'target')}
                </div>
            </div>
            <div id="viz-stream-hint" class="viz-stream-hint"></div>
        </div>
        <div id="viz-stream-popover" class="viz-stream-popover" style="display:none;"></div>
    `;

    requestAnimationFrame(() => {
        setupStreamEditor(sourceRole, targetRole, streams);
    });
}

function renderPortsForEditor(role, side) {
    const ports = role.ports || [];

    const matchingPorts = ports.filter(port => {
        const dir = port.direction || 'bidirectional';
        return dir === 'bidirectional' || (side === 'source' ? dir === 'output' : dir === 'input');
    });

    let html = '';

    const roleLabel = side === 'source' ? `${escapeHtml(role.name)} (как источник)` : `${escapeHtml(role.name)} (как приёмник)`;
    html += `
        <div class="viz-port viz-port--role" data-port-id="__role__" data-role-id="${role.id}" data-side="${side}">
            <span class="viz-port__dot"></span>
            <span class="viz-port__label"><em>${roleLabel}</em></span>
        </div>
    `;

    matchingPorts.forEach(port => {
        const dirClass = port.direction ? `viz-port--${port.direction}` : 'viz-port--bidirectional';
        const dirLabel = port.direction === 'input' ? '← вход' : port.direction === 'output' ? 'выход →' : '↔';
        if (side === 'source') {
            html += `
                <div class="viz-port ${dirClass}" data-port-id="${port.id}" data-role-id="${role.id}" data-side="source">
                    <span class="viz-port__label">${escapeHtml(port.name)} <small>${dirLabel}</small></span>
                    <span class="viz-port__dot"></span>
                </div>
            `;
        } else {
            html += `
                <div class="viz-port ${dirClass}" data-port-id="${port.id}" data-role-id="${role.id}" data-side="target">
                    <span class="viz-port__dot"></span>
                    <span class="viz-port__label">${escapeHtml(port.name)} <small>${dirLabel}</small></span>
                </div>
            `;
        }
    });

    return html;
}

function setupStreamEditor(sourceRole, targetRole, streams) {
    drawStreamLines(streams);
    setupPortClickHandlers(sourceRole, targetRole, streams);
    setupStreamResizeObserver(streams);
    setupLineClickHandlers(streams);

    const container = document.getElementById('viz-stream-container');
    if (container) {
        container.addEventListener('click', function (e) {
            if (e.target === this || e.target.closest('.viz-stream-canvas')) {
                hideStreamPopover();
            }
        });
    }
}

function getEditorCoords(roleId, portId, side) {
    const svg = document.getElementById('viz-stream-canvas');
    const container = document.getElementById('viz-stream-container');
    if (!svg || !container) return null;

    const svgRect = svg.getBoundingClientRect();

    if (portId) {
        const portEl = document.querySelector(`.viz-port[data-port-id="${portId}"]`);
        if (!portEl) return null;
        const dot = portEl.querySelector('.viz-port__dot');
        const el = dot || portEl;
        const elRect = el.getBoundingClientRect();
        return {
            x: elRect.left - svgRect.left + elRect.width / 2,
            y: elRect.top - svgRect.top + elRect.height / 2,
        };
    }

    const roleBlock = document.querySelector(`.viz-role-block[data-role-id="${roleId}"]`);
    if (!roleBlock) return null;
    const blockRect = roleBlock.getBoundingClientRect();
    const x = side === 'source' ? blockRect.right - svgRect.left : blockRect.left - svgRect.left;
    return {
        x: x,
        y: blockRect.top - svgRect.top + blockRect.height / 2,
    };
}

function drawStreamLines(streams) {
    const group = document.getElementById('viz-stream-lines');
    if (!group) return;

    group.innerHTML = '';

    streams.forEach(stream => {
        const from = getEditorCoords(stream.source_role_id, stream.source_port_id, 'source');
        const to = getEditorCoords(stream.target_role_id, stream.target_port_id, 'target');
        if (!from || !to) return;

        const dx = Math.abs(to.x - from.x) * 0.4;
        const d = `M ${from.x} ${from.y} C ${from.x + dx} ${from.y}, ${to.x - dx} ${to.y}, ${to.x} ${to.y}`;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('class', 'viz-stream-line');
        path.setAttribute('data-stream-id', stream.id);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#27ae60');
        path.setAttribute('stroke-width', '2.5');
        path.setAttribute('marker-end', 'url(#viz-arrowhead)');
        path.setAttribute('title', stream.name);
        group.appendChild(path);

        if (stream.name) {
            const cx = (from.x + to.x) / 2;
            const cy = (from.y + to.y) / 2;
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', cx);
            text.setAttribute('y', cy - 6);
            text.setAttribute('class', 'viz-stream-label');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', '#1f7f46');
            text.setAttribute('font-size', '11');
            text.setAttribute('pointer-events', 'none');
            text.textContent = stream.name;
            group.appendChild(text);
        }
    });
}

function getPortDisplayName(roleId, portId) {
    if (!portId || portId === '__role__') return 'вся роль';
    const role = getRoleById(roleId);
    const port = role?.ports?.find(p => p.id === portId);
    return port?.name || '(порт удалён)';
}

function setupLineClickHandlers(streams) {
    const group = document.getElementById('viz-stream-lines');
    if (!group) return;

    group.addEventListener('click', function (e) {
        const line = e.target.closest('.viz-stream-line');
        if (!line) return;

        const streamId = line.getAttribute('data-stream-id');
        const sourceRoleId = document.getElementById('stream-source-role-id').value;
        const targetRoleId = document.getElementById('stream-target-role-id').value;
        const allStreams = getRoleStreams(sourceRoleId, targetRoleId);
        const stream = allStreams.find(s => s.id === streamId);
        if (!stream) return;

        document.querySelectorAll('.viz-stream-line').forEach(l => {
            l.setAttribute('stroke', '#27ae60');
            l.setAttribute('marker-end', 'url(#viz-arrowhead)');
            l.classList.remove('viz-stream-line--selected');
        });
        line.setAttribute('stroke', '#e67e22');
        line.setAttribute('marker-end', 'url(#viz-arrowhead-selected)');
        line.classList.add('viz-stream-line--selected');

        window.editingStreamId = streamId;
        document.getElementById('stream-name').value = stream.name;
        document.getElementById('stream-description').value = stream.description || '';
        document.getElementById('stream-source-port').innerHTML = renderPortOptions(
            document.getElementById('stream-source-role-id').value,
            stream.source_port_id
        );
        document.getElementById('stream-target-port').innerHTML = renderPortOptions(
            document.getElementById('stream-target-role-id').value,
            stream.target_port_id
        );
        clearPortSelection();

        const hint = document.getElementById('viz-stream-hint');
        if (hint) hint.textContent = 'Кликните на другой порт, чтобы перенаправить поток';

        const rect = line.getBoundingClientRect();
        const containerRect = document.getElementById('viz-stream-popover').parentElement.getBoundingClientRect();
        showStreamPopover(rect.left - containerRect.left + rect.width / 2, rect.top - containerRect.top - 10, 'edit', stream);
    });
}

function clearPortSelection() {
    document.querySelectorAll('.viz-port--selected').forEach(el => el.classList.remove('viz-port--selected'));
    window.selectedSourcePortId = null;
    const hint = document.getElementById('viz-stream-hint');
    if (hint) hint.textContent = '';
}

let resizeObserver = null;

function setupStreamResizeObserver(streams) {
    if (resizeObserver) resizeObserver.disconnect();
    const container = document.getElementById('viz-stream-container');
    if (!container) return;
    resizeObserver = new ResizeObserver(() => {
        drawStreamLines(streams);
    });
    resizeObserver.observe(container);
}

function setupPortClickHandlers(sourceRole, targetRole, streams) {
    document.querySelectorAll('.viz-port[data-side="source"]').forEach(port => {
        port.addEventListener('click', function (e) {
            e.stopPropagation();
            const portId = this.getAttribute('data-port-id');

            if (window.editingStreamId) {
                applyPortUpdate('source', portId);
                return;
            }

            hideStreamPopover();
            document.querySelectorAll('.viz-port--selected').forEach(el => el.classList.remove('viz-port--selected'));
            this.classList.add('viz-port--selected');
            window.selectedSourcePortId = portId;
            const hint = document.getElementById('viz-stream-hint');
            if (hint) hint.textContent = 'Выберите порт-приёмник справа';
        });
    });

    document.querySelectorAll('.viz-port[data-side="target"]').forEach(port => {
        port.addEventListener('click', function (e) {
            e.stopPropagation();

            if (window.editingStreamId) {
                const portId = this.getAttribute('data-port-id');
                applyPortUpdate('target', portId);
                return;
            }

            const sourcePortId = window.selectedSourcePortId;
            if (!sourcePortId) {
                const hint = document.getElementById('viz-stream-hint');
                if (hint) hint.textContent = 'Сначала выберите порт-источник слева';
                return;
            }

            const targetPortId = this.getAttribute('data-port-id');
            clearPortSelection();

            const rect = this.querySelector('.viz-port__dot')?.getBoundingClientRect() || this.getBoundingClientRect();
            const containerRect = document.getElementById('viz-stream-popover').parentElement.getBoundingClientRect();
            showStreamPopover(
                rect.left - containerRect.left + rect.width / 2,
                rect.top - containerRect.top - 10,
                'create',
                { source_port_id: sourcePortId, target_port_id: targetPortId }
            );
        });
    });
}

async function applyPortUpdate(side, portId) {
    const streamId = window.editingStreamId;
    if (!streamId) return;

    const moduleId = window.currentObjectData?.id;
    const sourceRoleId = document.getElementById('stream-source-role-id').value;
    const targetRoleId = document.getElementById('stream-target-role-id').value;
    const allStreams = getRoleStreams(sourceRoleId, targetRoleId);
    const stream = allStreams.find(s => s.id === streamId);
    if (!stream) return;

    const newSourcePortId = side === 'source' ? portId : stream.source_port_id;
    const newTargetPortId = side === 'target' ? portId : stream.target_port_id;

    try {
        const res = await fetch(`/api/modules/${moduleId}/role-streams`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_role_id: sourceRoleId,
                target_role_id: targetRoleId,
                source_port_id: newSourcePortId === '__role__' ? null : newSourcePortId,
                target_port_id: newTargetPortId === '__role__' ? null : newTargetPortId,
                name: stream.name,
                description: stream.description || null,
                stream_id: streamId,
            }),
        });
        if (!res.ok) throw new Error(await res.text());

        const savedStream = await res.json();
        upsertRoleStreamInCurrentData(savedStream);
        rerenderStreamsMatrix();

        const updatedStreams = getRoleStreams(sourceRoleId, targetRoleId);
        drawStreamLines(updatedStreams);

        document.getElementById('stream-source-port').innerHTML = renderPortOptions(sourceRoleId, savedStream.source_port_id);
        document.getElementById('stream-target-port').innerHTML = renderPortOptions(targetRoleId, savedStream.target_port_id);

        const popover = document.getElementById('viz-stream-popover');
        if (popover && popover.style.display === 'block') {
            const rect = popover.getBoundingClientRect();
            const parentRect = popover.parentElement.getBoundingClientRect();
            showStreamPopover(
                Math.max(4, Math.min(rect.left - parentRect.left, parentRect.width - 240)),
                Math.max(4, rect.top - parentRect.top),
                'edit',
                savedStream
            );
        }
        const hint = document.getElementById('viz-stream-hint');
        if (hint) hint.textContent = 'Порт обновлён';

        showToast('Порт обновлён', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

function showStreamPopover(x, y, mode, data) {
    const popover = document.getElementById('viz-stream-popover');
    if (!popover) return;

    if (mode === 'create') {
        popover.innerHTML = `
            <div class="viz-popover-form">
                <label>Выбрать существующий поток:</label>
                <input type="text" id="viz-search-stream" placeholder="Поиск потока..." class="viz-popover-input" oninput="searchExistingStreams(this.value)">
                <div id="viz-search-results" class="viz-search-results" style="display:none;"></div>
                <div class="viz-popover-divider">Или создать новый</div>
                <label>Название нового потока:</label>
                <input type="text" id="viz-new-stream-name" placeholder="Введите название..." class="viz-popover-input" onkeydown="if(event.key==='Enter')createStreamFromPopover('${data.source_port_id}', '${data.target_port_id}')">
                <div class="viz-popover-actions">
                    <button type="button" class="viz-popover-btn viz-popover-btn--primary" onclick="createStreamFromPopover('${data.source_port_id}', '${data.target_port_id}')">Создать</button>
                    <button type="button" class="viz-popover-btn" onclick="hideStreamPopover()">Отмена</button>
                </div>
            </div>
        `;
        const parentRect = popover.parentElement.getBoundingClientRect();
        popover.style.left = Math.max(4, Math.min(x, parentRect.width - 250)) + 'px';
        popover.style.top = Math.max(4, y) + 'px';
        popover.style.display = 'block';
        setTimeout(() => {
            const input = document.getElementById('viz-search-stream');
            if (input) input.focus();
        }, 100);
    } else if (mode === 'edit') {
        const srcRoleId = document.getElementById('stream-source-role-id').value;
        const tgtRoleId = document.getElementById('stream-target-role-id').value;
        const srcPortName = getPortDisplayName(srcRoleId, data.source_port_id);
        const tgtPortName = getPortDisplayName(tgtRoleId, data.target_port_id);
        popover.innerHTML = `
            <div class="viz-popover-form">
                <label>Название потока:</label>
                <input type="text" id="viz-edit-stream-name" value="${escapeHtml(data.name)}" class="viz-popover-input" onkeydown="if(event.key==='Enter')updateStreamFromPopover()">
                <label>Описание:</label>
                <textarea id="viz-edit-stream-desc" class="viz-popover-textarea">${escapeHtml(data.description || '')}</textarea>
                <div class="viz-popover-ports">
                    <div class="viz-popover-port-row">
                        <span class="viz-popover-port-label">Источник:</span>
                        <span class="viz-popover-port-name">${escapeHtml(srcPortName)}</span>
                    </div>
                    <div class="viz-popover-port-row">
                        <span class="viz-popover-port-label">Приёмник:</span>
                        <span class="viz-popover-port-name">${escapeHtml(tgtPortName)}</span>
                    </div>
                </div>
                <div class="viz-popover-note">Кликните на другой порт на схеме, чтобы перенаправить поток</div>
                <div class="viz-popover-actions">
                    <button type="button" class="viz-popover-btn viz-popover-btn--primary" onclick="updateStreamFromPopover()">Сохранить</button>
                    <button type="button" class="viz-popover-btn viz-popover-btn--danger" onclick="deleteSingleRoleStream('${data.id}')">Удалить</button>
                    <button type="button" class="viz-popover-btn" onclick="hideStreamPopover()">Отмена</button>
                </div>
            </div>
        `;
        const parentRect = popover.parentElement.getBoundingClientRect();
        popover.style.left = Math.max(4, Math.min(x, parentRect.width - 240)) + 'px';
        popover.style.top = Math.max(4, y) + 'px';
        popover.style.display = 'block';
        setTimeout(() => {
            const input = document.getElementById('viz-edit-stream-name');
            if (input) input.focus();
        }, 100);
    }
}

function hideStreamPopover() {
    const popover = document.getElementById('viz-stream-popover');
    if (popover) popover.style.display = 'none';
    clearPortSelection();
    document.querySelectorAll('.viz-stream-line--selected').forEach(l => {
        l.setAttribute('stroke', '#27ae60');
        l.setAttribute('marker-end', 'url(#viz-arrowhead)');
        l.classList.remove('viz-stream-line--selected');
    });
    window.editingStreamId = null;
}

async function searchExistingStreams(query) {
    const resultsDiv = document.getElementById('viz-search-results');
    if (!resultsDiv) return;
    if (!query || query.trim().length < 1) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        return;
    }
    try {
        const res = await fetch(`/api/streams?query=${encodeURIComponent(query.trim())}&limit=10`);
        if (!res.ok) throw new Error(await res.text());
        const streams = await res.json();
        if (streams.length === 0) {
            resultsDiv.innerHTML = '<div class="viz-search-empty">Совпадений нет</div>';
        } else {
            resultsDiv.innerHTML = streams.map(s => `
                <button type="button" class="viz-search-item" onclick="selectExistingStream(decodeURIComponent('${encodeURIComponent(s.name)}'), decodeURIComponent('${encodeURIComponent(s.description || '')}'))">
                    <span>${escapeHtml(s.name)}</span>
                    ${s.description ? `<small>${escapeHtml(s.description)}</small>` : ''}
                </button>
            `).join('');
        }
        resultsDiv.style.display = 'block';
    } catch (err) {
        resultsDiv.style.display = 'none';
    }
}

function selectExistingStream(name, description) {
    const nameInput = document.getElementById('viz-new-stream-name');
    const searchInput = document.getElementById('viz-search-stream');
    if (nameInput) nameInput.value = name;
    if (searchInput) searchInput.value = name;
    const resultsDiv = document.getElementById('viz-search-results');
    if (resultsDiv) resultsDiv.style.display = 'none';
}

function createStreamFromPopover(sourcePortId, targetPortId) {
    const name = document.getElementById('viz-new-stream-name')?.value.trim();
    if (!name) {
        showToast('Введите название потока', 'error');
        return;
    }

    document.getElementById('stream-name').value = name;
    document.getElementById('stream-description').value = '';
    window.editingStreamId = null;

    const srcPort = sourcePortId === '__role__' || !sourcePortId ? null : sourcePortId;
    const tgtPort = targetPortId === '__role__' || !targetPortId ? null : targetPortId;

    hideStreamPopover();
    saveRoleStream(srcPort, tgtPort);
}

function updateStreamFromPopover() {
    const name = document.getElementById('viz-edit-stream-name')?.value.trim();
    if (!name) {
        showToast('Введите название потока', 'error');
        return;
    }

    document.getElementById('stream-name').value = name;
    document.getElementById('stream-description').value = document.getElementById('viz-edit-stream-desc')?.value.trim() || '';

    const sid = window.editingStreamId;
    hideStreamPopover();
    window.editingStreamId = sid;
    saveRoleStream();
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
                        <button onclick="showCreateParentModal()" title="Create new parent module" style="background: #4CAF50;">+ New Parent</button>
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
                    <button onclick="showCreateParentModal()" title="Create new parent module" style="background: #4CAF50;">+ New Parent</button>
                </div>
            `;
            container.appendChild(title);
            container.appendChild(newList);
            container.appendChild(addParentSection);
        }

        // Добавляем возможность удаления детей (теперь таблица вместо списка)
        const childrenTable = document.querySelector('.children-table');
        if (childrenTable) {
            // Добавляем кнопки Remove и Add к строкам таблицы
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
                    
                    const addBtn = document.createElement('button');
                    addBtn.className = 'add-same-btn';
                    addBtn.textContent = '+ Same';
                    addBtn.title = 'Add another relation to this child';
                    addBtn.style.marginLeft = '4px';
                    addBtn.style.background = '#4CAF50';
                    addBtn.style.color = 'white';
                    addBtn.style.border = 'none';
                    addBtn.style.borderRadius = '3px';
                    addBtn.style.fontSize = '12px';
                    addBtn.style.cursor = 'pointer';
                    addBtn.onclick = () => quickAddSameChild(row.dataset.childId, row.querySelector('.child-link, .child-link-expanded')?.textContent || '');
                    nameCell.appendChild(addBtn);
                }
            });
            
            // Добавляем кнопку Remove к развернутым строкам (без + - он только в свернутом режиме)
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
                        <button onclick="showCreateChildModal()" title="Create new child module" style="background: #4CAF50;">+ New Child</button>
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
                    <button onclick="showCreateChildModal()" title="Create new child module" style="background: #4CAF50;">+ New Child</button>
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

function getDefaultRelationCoordinates() {
    return { x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0 };
}

function getRelationInput(type) {
    return document.getElementById(`search-${type}-input`);
}

function resetRelationInput(type) {
    selectedRelId = null;
    selectedRelType = null;

    const input = getRelationInput(type);
    if (input) input.value = '';

    const resultsDiv = document.getElementById(`${type}-search-results`);
    if (resultsDiv) resultsDiv.style.display = 'none';
}

function getTypedRelationName(type) {
    const input = getRelationInput(type);
    return input?.value.trim() || '';
}

function ensureChildrenTable() {
    const existingTable = document.querySelector('.children-table');
    if (existingTable) return existingTable;

    const addChildSection = document.getElementById('add-child-section');
    if (!addChildSection) return null;

    const table = document.createElement('table');
    table.className = 'children-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th style="padding: 8px; border-bottom: 2px solid #ccc; text-align: left;">Module</th>
                <th style="padding: 8px; border-bottom: 2px solid #ccc; text-align: center; width: 80px;">Count</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    addChildSection.before(table);
    return table;
}

async function searchModulesForRelation(query, type) {
    const resultsDiv = document.getElementById(`${type}-search-results`);
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/basic_object?name=${encodeURIComponent(query)}`);
        const modules = await response.json();
        
        const availableModules = modules.filter(m => m.id !== window.currentObjectData.id);
        if (availableModules.length === 0) {
            const newButtonLabel = type === 'child' ? '+ New Child' : '+ New Parent';
            resultsDiv.innerHTML = `<div class="search-result-item">No results. Use ${newButtonLabel} to create one.</div>`;
        } else {
            resultsDiv.innerHTML = availableModules
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
    const input = getRelationInput(type);
    if (input) input.value = name;
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
        const newButtonLabel = type === 'child' ? '+ New Child' : '+ New Parent';
        showToast(`Please select a module from the search results or use ${newButtonLabel}`, 'error');
        return;
    }
    
    const name = getRelationInput(type)?.value || '';
    
    // Координаты по умолчанию (нулевые)
    const coords = getDefaultRelationCoordinates();
    
    if (type === 'child') {
        // Для детей добавляем строку в таблицу
        const table = ensureChildrenTable();
        
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
            
            // Инициализируем массив если его нет
            if (!window.childrenDepthData) {
                window.childrenDepthData = [];
            }
            window.childrenDepthData.push({
                child_id: selectedRelId,
                parent_child_module_id: null,
                depth: 1
            });
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
    resetRelationInput(type);
}

async function createBasicObjectForRelation(name) {
    const data = window.currentObjectData || {};
    const response = await fetch('/api/basic_object/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            author: data.author || 'unknown',
            description: '',
            is_assembly: false,
            is_shell: false
        })
    });

    if (response.ok) return response.json();

    const error = await response.json();
    throw new Error(error.detail || 'Failed to create module');
}

async function linkCreatedModuleToCurrent(type, moduleId) {
    const data = window.currentObjectData;
    if (!data?.id) throw new Error('Current module ID not found');

    const relation = { id: moduleId, coordinates: getDefaultRelationCoordinates() };
    const payload = type === 'child'
        ? { added_children: [relation] }
        : { added_parents: [relation] };

    const response = await fetch(`/api/basic_object/${data.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (response.ok) return;

    const error = await response.json();
    throw new Error(error.detail || 'Failed to link module');
}

function appendCreatedRelationToView(type, moduleId, name) {
    const coords = getDefaultRelationCoordinates();

    if (type === 'child') {
        const table = ensureChildrenTable();
        if (!table) return;

        const row = document.createElement('tr');
        row.dataset.childId = moduleId;
        row.dataset.coordinates = JSON.stringify(coords);
        row.className = 'child-group-row';
        row.innerHTML = `
            <td style="padding: 8px; border-bottom: 1px solid #eee;">
                <a href="/basic_object/${moduleId}">${name}</a>
                <span style="font-size: 11px; color: #666; margin-left: 10px;">(Created)</span>
                <button class="remove-btn" onclick="this.parentElement.parentElement.dataset.removed='true'; this.parentElement.parentElement.style.display='none';" style="margin-left: 8px; font-size: 11px;">Remove</button>
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                <input type="number" class="child-depth-input single-depth"
                    data-child-id="${moduleId}"
                    data-pcm-id=""
                    min="0" max="10" value="1"
                    style="width: 50px; padding: 4px; text-align: center;">
            </td>
        `;
        table.querySelector('tbody').appendChild(row);
        return;
    }

    const list = document.getElementById('parentsList');
    if (!list) return;

    const li = document.createElement('li');
    li.dataset.id = moduleId;
    li.dataset.coordinates = JSON.stringify(coords);
    li.innerHTML = `
        <a href="/basic_object/${moduleId}">${name}</a>
        <span style="font-size: 11px; color: #666; margin-left: 10px;">(Created)</span>
        <button class="remove-btn" onclick="this.parentElement.dataset.removed='true'; this.parentElement.style.display='none';">Remove</button>
    `;
    list.appendChild(li);
}

async function quickAddSameChild(childId, childName) {
    const data = window.currentObjectData;
    const payload = { 
        added_children: [{ id: childId, coordinates: { x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0 } }] 
    };
    
    try {
        const response = await fetch(`/api/basic_object/${data.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            showToast(`Added "${childName}" as child`, 'success');
            updateChildBadge(childId);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to add child', 'error');
        }
    } catch (e) {
        console.error('Error adding child:', e);
        showToast('Error adding child', 'error');
    }
}

function updateChildBadge(childId) {
    const childrenTable = document.querySelector('.children-table');
    if (!childrenTable) return;
    
    const groupRow = childrenTable.querySelector(`tr.child-group-row[data-child-id="${childId}"]`);
    if (!groupRow) return;
    
    const existingBadge = groupRow.querySelector('.child-count-badge');
    const childLink = groupRow.querySelector('.child-link');
    
    if (existingBadge) {
        const currentCount = parseInt(existingBadge.textContent.replace('×', '')) || 2;
        existingBadge.textContent = `×${currentCount + 1}`;
    } else {
        const badge = document.createElement('span');
        badge.className = 'child-count-badge expand-badge';
        badge.style.cursor = 'pointer';
        badge.title = 'Click to expand';
        badge.textContent = '×2';
        badge.dataset.group = groupRow.dataset.groupIndex;
        badge.addEventListener('click', function() {
            const groupIndex = this.dataset.group;
            const expandedRows = document.querySelectorAll(`.child-expanded-row[data-parent-group="${groupIndex}"]`);
            const isVisible = expandedRows[0] && expandedRows[0].style.display !== 'none';
            expandedRows.forEach(row => row.style.display = isVisible ? 'none' : 'table-row');
            this.textContent = isVisible ? `×${expandedRows.length}` : `▼×${expandedRows.length}`;
        });
        if (childLink) {
            childLink.insertAdjacentElement('afterend', badge);
        }
    }
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

function attachScadSectionsToTab() {
    const slot = document.getElementById('module-scad-tab-slot');
    const source = document.getElementById('module-extra-sections-source');
    if (!slot || !source) return;
    if (slot.childElementCount > 0) return;
    while (source.firstElementChild) {
        slot.appendChild(source.firstElementChild);
    }
    source.style.display = 'none';
}

function setActiveModuleTab(tabId) {
    const tabsContainer = document.getElementById('module-detail-tabs');
    if (!tabsContainer) return;
    const buttons = tabsContainer.querySelectorAll('.module-tab-btn');
    const panels = document.querySelectorAll('[data-module-tab-panel]');
    buttons.forEach(button => {
        button.classList.toggle('active', button.dataset.moduleTab === tabId);
    });
    panels.forEach(panel => {
        panel.classList.toggle('active', panel.dataset.moduleTabPanel === tabId);
    });
    if (tabId === 'scad' && typeof ensureThreeViewerInitialized === 'function') {
        ensureThreeViewerInitialized();
    }
}

function initModuleDetailsTabs() {
    const tabsContainer = document.getElementById('module-detail-tabs');
    if (!tabsContainer) return;
    attachScadSectionsToTab();
    const buttons = tabsContainer.querySelectorAll('.module-tab-btn');
    if (buttons.length === 0) return;
    buttons.forEach(button => {
        button.addEventListener('click', () => setActiveModuleTab(button.dataset.moduleTab));
    });
    setActiveModuleTab('overview');
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

async function loadRolesForSelect(selectId, moduleId) {
    try {
        const url = moduleId ? `/api/modules/${moduleId}/roles` : '/api/roles?limit=100';
        const response = await fetch(url);
        if (!response.ok) return;
        const roles = await response.json();
        const select = document.getElementById(selectId);
        if (!select) return;
        roles.forEach(role => {
            const opt = document.createElement('option');
            opt.value = role.name;
            opt.textContent = role.name + (role.description ? ` (${role.description})` : '');
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Error loading roles:', e);
    }
}

function showCreateChildModal() {
    const modal = document.getElementById('create-child-modal');
    if (!modal) return;

    document.getElementById('create-child-name').value = getTypedRelationName('child');

    const currentId = window.currentObjectData?.id;
    document.getElementById('create-child-role').innerHTML = '<option value="">— без роли —</option>';
    if (currentId) {
        loadRolesForSelect('create-child-role', currentId);
    }
    modal.style.display = 'flex';
}

function hideCreateChildModal() {
    const modal = document.getElementById('create-child-modal');
    if (modal) modal.style.display = 'none';
}

function showCreateParentModal() {
    const modal = document.getElementById('create-parent-modal');
    if (!modal) return;

    document.getElementById('create-parent-name').value = getTypedRelationName('parent');
    modal.style.display = 'flex';
}

function hideCreateParentModal() {
    const modal = document.getElementById('create-parent-modal');
    if (modal) modal.style.display = 'none';
}

async function submitCreateParentModule() {
    const name = document.getElementById('create-parent-name').value.trim();
    if (!name) {
        showToast('Введите название модуля', 'error');
        return;
    }

    try {
        const result = await createBasicObjectForRelation(name);
        await linkCreatedModuleToCurrent('parent', result.id);
        appendCreatedRelationToView('parent', result.id, name);
        resetRelationInput('parent');
        hideCreateParentModal();
        showToast(`Родительский модуль "${name}" создан`, 'success');
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}

async function submitCreateChildModule() {
    const name = document.getElementById('create-child-name').value.trim();
    if (!name) {
        showToast('Введите название модуля', 'error');
        return;
    }
    const role = document.getElementById('create-child-role').value;
    const currentId = window.currentObjectData?.id;
    if (!currentId) {
        showToast('ID текущего модуля не найден', 'error');
        return;
    }

    const payload = {
        name: name,
        author: window.currentObjectData.author || 'unknown',
        is_assembly: false,
        is_shell: false,
        parent_id: currentId,
        coordinates: {x: 0, y: 0, z: 0, angle: 0, axis: {x: 0, y: 0, z: 1}}
    };
    if (role) {
        payload.role = role;
    }

    try {
        const response = await fetch('/api/basic_object/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Ошибка создания модуля');
        }
        const result = await response.json();
        showToast(`Дочерний модуль "${name}" создан`, 'success');
        resetRelationInput('child');
        hideCreateChildModal();
        loadModuleInfo();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
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
        const detailsRoot = document.getElementById('objectDetails');
        if (detailsRoot) {
            detailsRoot.innerHTML = renderObjectDetails(data);
            initModuleDetailsTabs();
        } else if (container) {
            container.innerHTML = renderObjectDetails(data);
            initModuleDetailsTabs();
        }
    } catch (error) {
        console.error('Ошибка обновления данных:', error);
    }
}

// =====================================================================
// Матрица ролей
// =====================================================================

function renderRolesMatrix(data) {
    window.rolesMatrixCollapsed = window.rolesMatrixCollapsed || new Set();
    window.rolesMatrixChildrenCollapsed = window.rolesMatrixChildrenCollapsed || new Set();
    const parentId = data.id;
    const hasChildren = Array.isArray(data.children) && data.children.length > 0;
    const childrenHint = hasChildren
        ? ''
        : '<div class="info-message" style="margin-bottom:8px;">У модуля нет дочерних модулей. Можно управлять списком ролей и удалять лишние роли.</div>';

    const addRoleFormHtml = `
        <div id="roles-matrix-add-form" class="roles-matrix__add-form" style="display:none;">
            <div class="roles-matrix__search-wrap">
                <input
                    type="text"
                    id="roles-matrix-new-name"
                    placeholder="Название роли"
                    class="roles-matrix__input"
                    oninput="searchRolesForMatrix(this.value)"
                >
                <div id="roles-matrix-search-results" class="stream-search-results" style="display:none;"></div>
            </div>
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
            ${childrenHint}
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

function renderRoleLink(roleId, roleName) {
    if (!roleId) return escapeHtml(roleName || '—');
    return `<a href="/roles/${roleId}" class="role-link">${escapeHtml(roleName || roleId)}</a>`;
}

function rolesMatrixEnableEdit(parentId) {
    const data = window.currentObjectData;
    window.selectedExistingRole = null;
    document.getElementById('roles-matrix-edit-btn').style.display = 'none';
    document.getElementById('roles-matrix-done-btn').style.display = 'inline-block';

    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    wrapper.innerHTML = buildRolesMatrixTable(data, true, parentId);

    document.getElementById('roles-matrix-add-form').style.display = 'flex';
}

async function rolesMatrixDisableEdit(parentId) {
    await rolesMatrixRefreshCurrentData(parentId);
    resetRolesSearchSelection();
    const data = window.currentObjectData;
    document.getElementById('roles-matrix-edit-btn').style.display = 'inline-block';
    document.getElementById('roles-matrix-done-btn').style.display = 'none';

    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    wrapper.innerHTML = buildRolesMatrixTable(data, false, parentId);

    document.getElementById('roles-matrix-add-form').style.display = 'none';
    rerenderStreamsMatrix();
}

function buildRolesMatrixTable(data, editMode, parentId) {
    const roles = data.roles || [];
    const childLinks = Array.isArray(data.children_with_coordinates) ? data.children_with_coordinates : [];
    const collapsed = window.rolesMatrixCollapsed || new Set();
    const childrenCollapsed = window.rolesMatrixChildrenCollapsed || new Set();

    const groupedChildren = {};
    childLinks.forEach(link => {
        if (!groupedChildren[link.child_id]) groupedChildren[link.child_id] = [];
        groupedChildren[link.child_id].push(link);
    });

    const headerCells = roles.map(role => {
        const isCollapsed = collapsed.has(role.id);
        const collapseIcon = isCollapsed ? '›' : '‹';
        const collapseTitle = isCollapsed ? 'Развернуть' : 'Свернуть';
        const collapseBtn = `<button class="roles-matrix__collapse-btn" onclick="rolesMatrixToggleColumn('${role.id}')" title="${collapseTitle}">${collapseIcon}</button>`;
        const editBtn = editMode
            ? `<button class="roles-matrix__edit-role-btn" onclick="rolesMatrixInlineEdit(event, '${parentId}', '${role.id}', '${escapeHtml(role.name)}', '${escapeHtml(role.description || '')}')" title="Редактировать роль">✎</button>`
            : '';
        const deleteBtn = editMode
            ? `<button class="roles-matrix__delete-role-btn" onclick="rolesMatrixDeleteColumn('${parentId}', '${role.id}', '${escapeHtml(role.name)}')" title="Удалить роль из модуля">×</button>`
            : '';
        const collapsedClass = isCollapsed ? ' roles-matrix__col--collapsed' : '';
        return `<th class="roles-matrix__th${collapsedClass}" data-role-col="${role.id}" title="${escapeHtml(role.description || '')}">
            <div class="roles-matrix__th-inner" id="role-header-${role.id}">
                ${collapseBtn}
                <span class="roles-matrix__col-label">${renderRoleLink(role.id, role.name)}</span>
                ${editBtn}
                ${deleteBtn}
            </div>
        </th>`;
    }).join('');

    const bodyRows = Object.keys(groupedChildren).map(childId => {
        const group = groupedChildren[childId];
        const hasCopies = group.length > 1;
        const groupExpanded = hasCopies && childrenCollapsed.has(childId);
        const name = window.objectNamesCache && window.objectNamesCache[childId] ? escapeHtml(window.objectNamesCache[childId]) : childId;
        const toggleBtn = hasCopies
            ? `<button class="roles-matrix__collapse-btn" onclick="rolesMatrixToggleChildGroup('${childId}')" title="${groupExpanded ? 'Collapse copies' : 'Expand copies'}">${groupExpanded ? '▾' : '▸'}</button>`
            : '';

        const groupCells = roles.map(role => {
            const isCollapsed = collapsed.has(role.id);
            const collapsedClass = isCollapsed ? ' roles-matrix__col--collapsed' : '';
            const checked = group.some(link => getLinkRoleIds(link).includes(role.id)) ? 'checked' : '';
            if (editMode) {
                return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}">
                    <input type="checkbox" class="roles-matrix__checkbox" ${checked} onchange="rolesMatrixToggleAssignment(this, '${childId}', '${role.id}')">
                </td>`;
            }
            return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}">
                <input type="checkbox" class="roles-matrix__checkbox roles-matrix__checkbox--readonly" ${checked} tabindex="-1">
            </td>`;
        }).join('');

        let html = `<tr data-child-id="${childId}" class="roles-matrix__group-row">
            <td class="roles-matrix__child-name">
                <div style="display:flex; align-items:center; gap:6px;">
                    ${toggleBtn}
                    <a href="/basic_object/${childId}">${name}</a>
                    ${hasCopies ? `<span class="child-count-badge" title="Copies">&times;${group.length}</span>` : ''}
                </div>
            </td>
            ${groupCells}
            ${editMode ? '<td class="roles-matrix__th roles-matrix__th--add"></td>' : ''}
        </tr>`;

        if (hasCopies && groupExpanded) {
            html += group.map((link, index) => {
                const pcmId = link.parent_child_module_id;
                const copyLabel = hasCopies ? `Copy #${index + 1}` : 'Copy #1';
                const cells = roles.map(role => {
                    const isCollapsed = collapsed.has(role.id);
                    const roleIds = getLinkRoleIds(link);
                    const checked = roleIds.includes(role.id) ? 'checked' : '';
                    const collapsedClass = isCollapsed ? ' roles-matrix__col--collapsed' : '';
                    if (editMode) {
                        return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}">
                            <input type="checkbox" class="roles-matrix__checkbox" ${checked} onchange="rolesMatrixToggleAssignmentForCopy(this, '${pcmId}', '${role.id}')">
                        </td>`;
                    }
                    return `<td class="roles-matrix__cell${collapsedClass}" data-role-col="${role.id}">
                        <input type="checkbox" class="roles-matrix__checkbox roles-matrix__checkbox--readonly" ${checked} tabindex="-1">
                    </td>`;
                }).join('');
                return `<tr class="roles-matrix__copy-row" data-parent-child-id="${pcmId || ''}">
                    <td class="roles-matrix__child-name" style="padding-left:26px;">
                        <span style="color:#666;">${copyLabel}</span>
                    </td>
                    ${cells}
                    ${editMode ? '<td class="roles-matrix__th roles-matrix__th--add"></td>' : ''}
                </tr>`;
            }).join('');
        }

        return html;
    }).join('');

    return `<table class="roles-matrix">
        <thead><tr>
            <th class="roles-matrix__th roles-matrix__th--child">Module</th>
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

function rolesMatrixToggleChildGroup(childId) {
    if (!window.rolesMatrixChildrenCollapsed) window.rolesMatrixChildrenCollapsed = new Set();
    if (window.rolesMatrixChildrenCollapsed.has(childId)) {
        window.rolesMatrixChildrenCollapsed.delete(childId);
    } else {
        window.rolesMatrixChildrenCollapsed.add(childId);
    }
    const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
    const parentId = window.currentObjectData?.id;
    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    if (!wrapper || !parentId) return;
    wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
}

function getLinkRoleIds(link) {
    if (Array.isArray(link.role_ids)) return [...link.role_ids];
    return link.role_id ? [link.role_id] : [];
}

async function rolesMatrixToggleAssignment(checkbox, childId, roleId) {
    const links = (window.currentObjectData.children_with_coordinates || [])
        .filter(item => item.child_id === childId);

    if (links.length === 0) {
        checkbox.checked = !checkbox.checked;
        showToast('Error: child link not found', 'error');
        return;
    }

    try {
        await Promise.all(links.map(async (link) => {
            const currentRoleIds = getLinkRoleIds(link);
            const nextRoleIds = checkbox.checked
                ? (currentRoleIds.includes(roleId) ? currentRoleIds : [...currentRoleIds, roleId])
                : currentRoleIds.filter(id => id !== roleId);

            const res = await fetch(`/api/parent_child_module/${link.parent_child_module_id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role_ids: nextRoleIds }),
            });
            if (!res.ok) throw new Error(await res.text());

            link.role_ids = nextRoleIds;
            link.role_id = nextRoleIds.length > 0 ? nextRoleIds[0] : null;
        }));

        // Перерисовываем чтобы синхронизировать состояние групп/копий
        const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
        const parentId = window.currentObjectData?.id;
        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        if (wrapper && parentId) {
            wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
        }
    } catch (err) {
        checkbox.checked = !checkbox.checked;
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function rolesMatrixToggleAssignmentForCopy(checkbox, parentChildModuleId, roleId) {
    if (!parentChildModuleId) {
        checkbox.checked = !checkbox.checked;
        showToast('Error: parent-child link is missing', 'error');
        return;
    }

    const links = window.currentObjectData.children_with_coordinates || [];
    const target = links.find(item => item.parent_child_module_id === parentChildModuleId);
    if (!target) {
        checkbox.checked = !checkbox.checked;
        showToast('Error: copy link not found', 'error');
        return;
    }

    const currentRoleIds = getLinkRoleIds(target);
    const nextRoleIds = checkbox.checked
        ? (currentRoleIds.includes(roleId) ? currentRoleIds : [...currentRoleIds, roleId])
        : currentRoleIds.filter(id => id !== roleId);
    try {
        const res = await fetch(`/api/parent_child_module/${parentChildModuleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role_ids: nextRoleIds }),
        });
        if (!res.ok) throw new Error(await res.text());

        target.role_ids = nextRoleIds;
        target.role_id = nextRoleIds.length > 0 ? nextRoleIds[0] : null;
        const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
        const parentId = window.currentObjectData?.id;
        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        if (wrapper && parentId) {
            wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
        }
    } catch (err) {
        checkbox.checked = !checkbox.checked;
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function rolesMatrixAddColumn(parentId) {
    const nameInput = document.getElementById('roles-matrix-new-name');
    const descInput = document.getElementById('roles-matrix-new-desc');
    const name = nameInput.value.trim();
    const selectedRole = window.selectedExistingRole;
    if (!name) {
        showToast('Введите название роли', 'error');
        return;
    }

    const body = selectedRole
        ? { role_id: selectedRole.id }
        : { name, description: descInput.value.trim() || null };

    try {
        const res = await fetch(`/api/modules/${parentId}/roles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(await res.text());
        const newRole = await res.json();

        if (!window.currentObjectData.roles) window.currentObjectData.roles = [];
        if (!window.currentObjectData.roles.some(role => role.id === newRole.id)) {
            window.currentObjectData.roles.push(newRole);
        }

        nameInput.value = '';
        descInput.value = '';
        resetRolesSearchSelection();

        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, true, parentId);
        rerenderStreamsMatrix();
        showToast('Роль добавлена', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function searchRolesForMatrix(query) {
    const resultsDiv = document.getElementById('roles-matrix-search-results');
    if (!resultsDiv) return;

    const normalizedQuery = (query || '').trim();
    if (window.selectedExistingRole && window.selectedExistingRole.name !== normalizedQuery) {
        window.selectedExistingRole = null;
    }
    if (!normalizedQuery) {
        resetRolesSearchSelection();
        return;
    }

    try {
        const res = await fetch(`/api/roles?query=${encodeURIComponent(normalizedQuery)}&limit=20`);
        if (!res.ok) throw new Error(await res.text());
        const roles = await res.json();

        if (roles.length === 0) {
            resultsDiv.innerHTML = '<div class="stream-search-empty">Совпадений нет. Можно создать новую роль.</div>';
            resultsDiv.style.display = 'block';
            return;
        }

        const currentRoleIds = new Set((window.currentObjectData?.roles || []).map(role => role.id));
        resultsDiv.innerHTML = roles.map(role => {
            const assignedBadge = currentRoleIds.has(role.id)
                ? '<small class="roles-matrix__search-meta">Уже назначена этому модулю</small>'
                : '';
            const description = role.description ? `<small>${escapeHtml(role.description)}</small>` : '';
            return `
                <button
                    type="button"
                    class="stream-search-item"
                    onclick="selectRoleForMatrix('${role.id}', decodeURIComponent('${encodeURIComponent(role.name)}'), decodeURIComponent('${encodeURIComponent(role.description || '')}'))"
                >
                    <span>${escapeHtml(role.name)}</span>
                    ${description}
                    ${assignedBadge}
                </button>
            `;
        }).join('');
        resultsDiv.style.display = 'block';
    } catch (err) {
        resultsDiv.innerHTML = '<div class="stream-search-empty">Ошибка поиска ролей</div>';
        resultsDiv.style.display = 'block';
    }
}

function selectRoleForMatrix(roleId, name, description) {
    window.selectedExistingRole = {
        id: roleId,
        name,
        description: description || '',
    };
    const nameInput = document.getElementById('roles-matrix-new-name');
    const descInput = document.getElementById('roles-matrix-new-desc');
    const resultsDiv = document.getElementById('roles-matrix-search-results');
    if (nameInput) nameInput.value = name;
    if (descInput) descInput.value = description || '';
    if (resultsDiv) resultsDiv.style.display = 'none';
}

function resetRolesSearchSelection() {
    const resultsDiv = document.getElementById('roles-matrix-search-results');
    if (resultsDiv) {
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
    }
    window.selectedExistingRole = null;
}

async function rolesMatrixDeleteColumn(parentId, roleId, roleName) {
    if (!confirm(`Удалить роль "${roleName}" из модуля?`)) return;

    try {
        const res = await fetch(`/api/modules/${parentId}/roles/${roleId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());

        window.currentObjectData.roles = (window.currentObjectData.roles || []).filter(r => r.id !== roleId);
        const childLinks = window.currentObjectData.children_with_coordinates || [];
        childLinks.forEach(link => {
            if (link.role_id === roleId) link.role_id = null;
            if (Array.isArray(link.role_ids)) {
                link.role_ids = link.role_ids.filter(id => id !== roleId);
            }
        });
        window.currentObjectData.role_streams = (window.currentObjectData.role_streams || []).filter(stream =>
            stream.source_role_id !== roleId && stream.target_role_id !== roleId
        );

        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, true, parentId);
        rerenderStreamsMatrix();
        showToast('Роль удалена', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

function rolesMatrixInlineEdit(event, parentId, roleId, roleName, roleDesc) {
    event.stopPropagation();
    const headerDiv = document.getElementById(`role-header-${roleId}`);
    if (!headerDiv) return;

    const nameEscaped = escapeHtml(roleName);
    const descEscaped = escapeHtml(roleDesc || '');
    headerDiv.innerHTML = `
        <input type="text" id="role-edit-name-${roleId}" value="${nameEscaped}" class="roles-matrix__inline-input" placeholder="Название">
        <input type="text" id="role-edit-desc-${roleId}" value="${descEscaped}" class="roles-matrix__inline-input" placeholder="Описание">
        <button class="roles-matrix__inline-btn roles-matrix__inline-btn--save" onclick="rolesMatrixSaveInline('${parentId}','${roleId}')" title="Сохранить">✓</button>
        <button class="roles-matrix__inline-btn roles-matrix__inline-btn--cancel" onclick="rolesMatrixCancelInline(event, '${parentId}','${roleId}')" title="Отмена">✗</button>
    `;
}

async function rolesMatrixSaveInline(parentId, roleId) {
    const nameInput = document.getElementById(`role-edit-name-${roleId}`);
    const descInput = document.getElementById(`role-edit-desc-${roleId}`);
    const name = (nameInput?.value || '').trim();
    const description = (descInput?.value || '').trim() || null;

    if (!name) {
        showToast('Название роли не может быть пустым', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/modules/${parentId}/roles/${roleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description }),
        });
        if (!res.ok) throw new Error(await res.text());

        const roles = window.currentObjectData.roles || [];
        const role = roles.find(r => r.id === roleId);
        if (role) {
            role.name = name;
            role.description = description;
        }

        const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
        const wrapper = document.getElementById('roles-matrix-table-wrapper');
        if (wrapper && parentId) {
            wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
        }
        rerenderStreamsMatrix();
        showToast('Роль обновлена', 'success');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

function rolesMatrixCancelInline(event, parentId, roleId) {
    event.stopPropagation();
    const isEditMode = document.getElementById('roles-matrix-done-btn')?.style.display !== 'none';
    const wrapper = document.getElementById('roles-matrix-table-wrapper');
    if (wrapper && parentId) {
        wrapper.innerHTML = buildRolesMatrixTable(window.currentObjectData, isEditMode, parentId);
    }
}

async function rolesMatrixRefreshCurrentData(parentId) {
    try {
        const res = await fetch(`/api/basic_object/${parentId}?_=${Date.now()}`, {
            cache: 'no-store',
        });
        if (!res.ok) throw new Error(await res.text());
        window.currentObjectData = await res.json();
    } catch (err) {
        showToast('Ошибка обновления данных ролей: ' + err.message, 'error');
    }
}

function rolesMatrixHideAddForm() {
    document.getElementById('roles-matrix-add-form').style.display = 'none';
    document.getElementById('roles-matrix-new-name').value = '';
    document.getElementById('roles-matrix-new-desc').value = '';
}

// =====================================================================
// Interfaces Tab
// =====================================================================

let editingInterfaceId = null;

function renderInterfacesTab(data) {
    const ifaces = data.interfaces || [];
    const ifaceMappings = data.interface_mappings || [];
    const roles = getExternalInterfaceRoles(data);

    return `
        <div style="display:grid; gap:16px;">
            ${renderInterfacesListSection(ifaces, ifaceMappings, roles)}
            ${renderPortMappingSection(roles, ifaces, ifaceMappings, data.id, data.external_role_streams || [])}
        </div>
    `;
}

function getExternalInterfaceRoles(data) {
    const rolesById = {};
    (data.parent_edges || []).forEach(edge => {
        if (!edge.role_id) return;
        if (!rolesById[edge.role_id]) {
            rolesById[edge.role_id] = {
                id: edge.role_id,
                name: edge.role_name || edge.role_id,
                description: edge.role_description || '',
                parentIds: new Set(),
                ports: edge.ports || [],
            };
        }
        rolesById[edge.role_id].parentIds.add(edge.parent_id);
        if ((rolesById[edge.role_id].ports || []).length === 0 && Array.isArray(edge.ports)) {
            rolesById[edge.role_id].ports = edge.ports;
        }
    });
    return Object.values(rolesById).map(role => ({
        ...role,
        parentIds: Array.from(role.parentIds),
    }));
}

function getExternalInterfacePorts(data) {
    return getExternalInterfaceRoles(data)
        .flatMap(role => (role.ports || []).map(port => ({ ...port, roleName: role.name, roleId: role.id })));
}

function renderInterfacesListSection(ifaces, mappings = [], roles = []) {
    const portsById = {};
    roles.forEach(role => {
        (role.ports || []).forEach(port => {
            portsById[port.id] = { ...port, roleName: role.name };
        });
    });
    const mappingsByInterfaceId = {};
    mappings.forEach(mapping => {
        if (!mappingsByInterfaceId[mapping.interface_id]) {
            mappingsByInterfaceId[mapping.interface_id] = [];
        }
        mappingsByInterfaceId[mapping.interface_id].push(mapping);
    });

    const rows = ifaces.map(iface => {
        const paramsStr = iface.parameters
            ? Object.entries(iface.parameters).map(([k, v]) => `${k}: ${v}`).join(', ')
            : '—';
        const mandatoryLabel = iface.is_mandatory
            ? '<span style="color:#e74c3c;font-weight:600;">Mandatory</span>'
            : '<span style="color:#888;">Optional</span>';
        const serviceLabel = iface.is_service
            ? ' <span style="color:#3498db;">[Service]</span>'
            : '';
        const linkedPorts = (mappingsByInterfaceId[iface.id] || [])
            .map(mapping => {
                const port = portsById[mapping.role_port_id];
                if (!port) return null;
                return `${escapeHtml(port.roleName)} → ${escapeHtml(port.name)}`;
            })
            .filter(Boolean)
            .join('<br>');
        return `
            <tr>
                <td><strong>${escapeHtml(iface.name)}</strong></td>
                <td>${iface.direction}</td>
                <td>${escapeHtml(iface.physical_form || '—')}</td>
                <td style="font-size:12px;">${escapeHtml(paramsStr)}</td>
                <td style="font-size:12px;">${linkedPorts || '—'}</td>
                <td style="white-space:nowrap;">${mandatoryLabel}${serviceLabel}</td>
                <td>
                    <button class="btn-small" onclick="editInterface('${iface.id}')">✎</button>
                    <button class="btn-small" style="background:#e74c3c;" onclick="deleteInterface('${iface.id}')">×</button>
                </td>
            </tr>
        `;
    }).join('');

    const emptyRow = ifaces.length === 0
        ? '<tr><td colspan="7" style="color:#aaa;text-align:center;">Нет структурных интерфейсов</td></tr>'
        : '';

    return `
        <div class="section-card">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <h2 style="margin:0;">Structural Interfaces</h2>
                <div>
                    <button id="show-add-interface-btn" class="btn" onclick="showAddInterfaceForm()">+ Add Interface</button>
                    <button id="hide-add-interface-btn" class="btn btn-secondary" onclick="hideAddInterfaceForm()" style="display:none;">Cancel</button>
                </div>
            </div>

            <div id="interface-form-container" style="display:none; margin-top:12px; padding:12px; border:1px solid #ddd; border-radius:6px; background:#fafafa;">
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div>
                        <label>Name</label>
                        <input id="iface-name" type="text" placeholder="e.g. Клеммник питания" style="width:100%;padding:6px;">
                    </div>
                    <div>
                        <label>Direction</label>
                        <select id="iface-direction" style="width:100%;padding:6px;">
                            <option value="bidirectional">bidirectional</option>
                            <option value="input">input</option>
                            <option value="output">output</option>
                        </select>
                    </div>
                    <div>
                        <label>Physical Form</label>
                        <input id="iface-physical-form" type="text" placeholder="e.g. M12 4-pin" style="width:100%;padding:6px;">
                    </div>
                    <div>
                        <label>Mandatory</label>
                        <input id="iface-mandatory" type="checkbox" checked>
                    </div>
                    <div>
                        <label>Service</label>
                        <input id="iface-service" type="checkbox">
                    </div>
                    <div style="grid-column: span 2;">
                        <label>Parameters (JSON)</label>
                        <textarea id="iface-parameters" rows="3" placeholder='{"voltage": 24, "current_max": 15}' style="width:100%;padding:6px;font-family:monospace;font-size:12px;"></textarea>
                    </div>
                    <div style="grid-column: span 2;">
                        <label>Description</label>
                        <input id="iface-description" type="text" placeholder="Optional description" style="width:100%;padding:6px;">
                    </div>
                </div>
                <div style="margin-top:10px;display:flex;gap:8px;">
                    <button class="btn" onclick="saveInterface()">Save</button>
                    <button class="btn btn-secondary" onclick="hideAddInterfaceForm()">Cancel</button>
                </div>
            </div>

            <table class="detail-table" style="margin-top:12px;">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Direction</th>
                        <th>Physical Form</th>
                        <th>Parameters</th>
                        <th>Linked Ports</th>
                        <th>Flags</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>${rows}${emptyRow}</tbody>
            </table>
        </div>
    `;
}

function renderPortMappingSection(roles, ifaces, mappings, moduleId, externalStreams = []) {
    const allPorts = roles.flatMap(r => (r.ports || []).map(p => ({ ...p, roleName: r.name, roleId: r.id })));
    if (allPorts.length === 0) {
        return `
            <div class="section-card">
                <h2 style="margin-top:0;">Port-Interface Mapping</h2>
                <div class="info-message">У модуля нет внешних ролей с портами. Назначьте этому модулю роль в родительском модуле.</div>
            </div>
        `;
    }

    const mappedByPortId = {};
    mappings.forEach(m => {
        if (!mappedByPortId[m.role_port_id]) {
            mappedByPortId[m.role_port_id] = [];
        }
        mappedByPortId[m.role_port_id].push(m);
    });

    const rows = allPorts.map(port => {
        const portMappings = mappedByPortId[port.id] || [];
        const mappedIfaces = portMappings
            .map(mapping => ({
                mapping,
                iface: ifaces.find(i => i.id === mapping.interface_id),
            }))
            .filter(item => item.iface);
        const status = mappedIfaces.length > 0
            ? '<span style="color:#27ae60;font-weight:600;">✅ Linked</span>'
            : '<span style="color:#e74c3c;">❌ Not linked</span>';
        const ifaceName = mappedIfaces.length > 0
            ? mappedIfaces.map(item => escapeHtml(item.iface.name)).join('<br>')
            : '—';
        const unlinkBtns = mappedIfaces.map(item =>
            `<button class="btn-small" style="background:#e74c3c;" onclick="unlinkInterface('${item.mapping.id}')">Unlink ${escapeHtml(item.iface.name)}</button>`
        ).join(' ');
        const linkBtn = `<button class="btn-small" onclick="showLinkInterfaceModal('${port.id}', '${port.roleId}')">Link</button>`;
        const streamsHtml = renderPortMappingStreams(port, externalStreams);
        return `
            <tr>
                <td>${escapeHtml(port.roleName)}</td>
                <td><strong>${escapeHtml(port.name)}</strong> <small>(${port.direction})</small></td>
                <td>${streamsHtml}</td>
                <td>${ifaceName}</td>
                <td>${status}</td>
                <td>${linkBtn} ${unlinkBtns}</td>
            </tr>
        `;
    }).join('');
    const mappedPortIds = new Set(mappings.map(m => m.role_port_id));
    const coveredPorts = allPorts.filter(port => mappedPortIds.has(port.id)).length;

    return `
        <div class="section-card">
            <h2 style="margin-top:0;">Port-Interface Mapping</h2>
            <p><strong>${coveredPorts}/${allPorts.length}</strong> role ports are linked to interfaces.</p>
            <table class="detail-table">
                <thead>
                    <tr>
                        <th>Role</th>
                        <th>Port</th>
                        <th>Streams</th>
                        <th>Interface</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderPortMappingStreams(port, externalStreams) {
    const relatedStreams = externalStreams.filter(stream => {
        const isSourceRole = stream.source_role_id === port.roleId;
        const isTargetRole = stream.target_role_id === port.roleId;
        const sourceMatches = isSourceRole && (!stream.source_port_id || stream.source_port_id === port.id);
        const targetMatches = isTargetRole && (!stream.target_port_id || stream.target_port_id === port.id);
        return sourceMatches || targetMatches;
    });

    if (relatedStreams.length === 0) {
        return '—';
    }

    return relatedStreams.map(stream => {
        const isSource = stream.source_role_id === port.roleId;
        const currentPortId = isSource ? stream.source_port_id : stream.target_port_id;
        const otherRole = isSource ? stream.target_role_name : stream.source_role_name;
        const otherPort = isSource ? stream.target_port_name : stream.source_port_name;
        const direction = isSource ? 'out' : 'in';
        const portScope = currentPortId ? '' : ' <small>(role)</small>';
        const otherSide = [otherRole, otherPort].filter(Boolean).join(' / ');
        const parentName = stream.parent_module_name || stream.parent_module_id || '';
        return `
            <div style="font-size:12px;line-height:1.35;margin:2px 0;">
                <strong>${escapeHtml(stream.name)}</strong> <small>${direction}</small>${portScope}
                ${otherSide ? `<br><small>${escapeHtml(otherSide)}</small>` : ''}
                ${parentName ? `<br><small>parent: ${escapeHtml(parentName)}</small>` : ''}
            </div>
        `;
    }).join('');
}

function showAddInterfaceForm() {
    editingInterfaceId = null;
    document.getElementById('iface-name').value = '';
    document.getElementById('iface-direction').value = 'bidirectional';
    document.getElementById('iface-physical-form').value = '';
    document.getElementById('iface-parameters').value = '';
    document.getElementById('iface-description').value = '';
    document.getElementById('iface-mandatory').checked = true;
    document.getElementById('iface-service').checked = false;
    document.getElementById('interface-form-container').style.display = 'block';
    document.getElementById('show-add-interface-btn').style.display = 'none';
    document.getElementById('hide-add-interface-btn').style.display = 'inline-block';
}

function hideAddInterfaceForm() {
    document.getElementById('interface-form-container').style.display = 'none';
    document.getElementById('show-add-interface-btn').style.display = 'inline-block';
    document.getElementById('hide-add-interface-btn').style.display = 'none';
    editingInterfaceId = null;
}

async function saveInterface() {
    const moduleId = window.currentObjectData.id;
    const name = document.getElementById('iface-name').value.trim();
    if (!name) {
        showToast('Введите название интерфейса', 'error');
        return;
    }

    let parameters = null;
    const paramsText = document.getElementById('iface-parameters').value.trim();
    if (paramsText) {
        try {
            parameters = JSON.parse(paramsText);
        } catch (e) {
            showToast('Неверный формат JSON в параметрах', 'error');
            return;
        }
    }

    const body = {
        name,
        direction: document.getElementById('iface-direction').value,
        physical_form: document.getElementById('iface-physical-form').value.trim() || null,
        parameters,
        is_mandatory: document.getElementById('iface-mandatory').checked,
        is_service: document.getElementById('iface-service').checked,
        description: document.getElementById('iface-description').value.trim() || null,
    };

    try {
        const url = editingInterfaceId
            ? `/api/modules/${moduleId}/interfaces/${editingInterfaceId}`
            : `/api/modules/${moduleId}/interfaces`;
        const method = editingInterfaceId ? 'PATCH' : 'POST';

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка сохранения');
        }
        showToast(editingInterfaceId ? 'Интерфейс обновлён' : 'Интерфейс создан', 'success');
        hideAddInterfaceForm();
        await refreshObjectDetails();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function editInterface(interfaceId) {
    const data = window.currentObjectData;
    const iface = (data.interfaces || []).find(i => i.id === interfaceId);
    if (!iface) return;

    editingInterfaceId = interfaceId;
    document.getElementById('iface-name').value = iface.name || '';
    document.getElementById('iface-direction').value = iface.direction || 'bidirectional';
    document.getElementById('iface-physical-form').value = iface.physical_form || '';
    document.getElementById('iface-parameters').value = iface.parameters
        ? JSON.stringify(iface.parameters, null, 2)
        : '';
    document.getElementById('iface-description').value = iface.description || '';
    document.getElementById('iface-mandatory').checked = iface.is_mandatory !== false;
    document.getElementById('iface-service').checked = !!iface.is_service;
    document.getElementById('interface-form-container').style.display = 'block';
    document.getElementById('show-add-interface-btn').style.display = 'none';
    document.getElementById('hide-add-interface-btn').style.display = 'inline-block';
}

async function deleteInterface(interfaceId) {
    if (!confirm('Удалить этот интерфейс?')) return;
    const moduleId = window.currentObjectData.id;
    try {
        const res = await fetch(`/api/modules/${moduleId}/interfaces/${interfaceId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error((await res.json()).detail || 'Ошибка удаления');
        showToast('Интерфейс удалён', 'success');
        await refreshObjectDetails();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

// Link/Unlink interface mapping

async function showLinkInterfaceModal(portId, roleId) {
    const moduleId = window.currentObjectData.id;
    const ifaces = window.currentObjectData.interfaces || [];

    let roleName = '';
    const externalRoles = getExternalInterfaceRoles(window.currentObjectData || {});
    const role = externalRoles.find(r => r.id === roleId);
    if (role) roleName = role.name;

    const port = externalRoles
        .flatMap(r => (r.ports || []))
        .find(p => p.id === portId);
    const portName = port ? port.name : portId;

    if (ifaces.length === 0) {
        showToast('Сначала создайте интерфейсы для модуля', 'error');
        return;
    }

    const existingInterfaceIds = new Set(
        (window.currentObjectData.interface_mappings || [])
            .filter(mapping => mapping.role_port_id === portId)
            .map(mapping => mapping.interface_id)
    );
    const availableIfaces = ifaces.filter(i => !existingInterfaceIds.has(i.id));
    if (availableIfaces.length === 0) {
        showToast('Все интерфейсы модуля уже привязаны к этому порту', 'error');
        return;
    }

    const options = availableIfaces.map(i =>
        `<option value="${i.id}">${escapeHtml(i.name)}</option>`
    ).join('');

    const container = document.createElement('div');
    container.id = 'link-interface-modal';
    container.style.cssText = `
        position: fixed; inset: 0; background: rgba(0,0,0,0.4);
        display: flex; align-items: center; justify-content: center; z-index: 1000;
    `;
    container.innerHTML = `
        <div style="background:#fff; border-radius:8px; padding:20px; min-width:400px; box-shadow:0 4px 20px rgba(0,0,0,0.2);">
            <h3>Link Interface to Port</h3>
            <p><strong>Role:</strong> ${escapeHtml(roleName)}<br><strong>Port:</strong> ${escapeHtml(portName)}</p>
            <label>Select Interface:</label>
            <select id="link-interface-select" style="width:100%; padding:8px; margin:8px 0;">${options}</select>
            <div style="display:flex; gap:8px; margin-top:12px;">
                <button class="btn" onclick="confirmLinkInterface('${portId}')">Link</button>
                <button class="btn btn-secondary" onclick="closeLinkInterfaceModal()">Cancel</button>
            </div>
        </div>
    `;
    document.body.appendChild(container);
}

function closeLinkInterfaceModal() {
    const el = document.getElementById('link-interface-modal');
    if (el) el.remove();
}

async function confirmLinkInterface(portId) {
    const moduleId = window.currentObjectData.id;
    const interfaceId = document.getElementById('link-interface-select').value;

    try {
        const res = await fetch(`/api/modules/${moduleId}/interface-mappings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role_port_id: portId, interface_id: interfaceId }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Ошибка создания маппинга');
        }
        showToast('Порт привязан к интерфейсу', 'success');
        closeLinkInterfaceModal();
        await refreshObjectDetails();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function unlinkInterface(mappingId) {
    if (!confirm('Отвязать интерфейс от порта?')) return;
    const moduleId = window.currentObjectData.id;
    try {
        const res = await fetch(`/api/modules/${moduleId}/interface-mappings/${mappingId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Ошибка удаления маппинга');
        showToast('Интерфейс отвязан', 'success');
        await refreshObjectDetails();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

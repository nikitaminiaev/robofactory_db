/**
 * Модуль для работы с историей Git
 * Визуализация графа коммитов и checkout
 */
const GitHistory = (function() {
    'use strict';

    let moduleId = null;
    let currentCommitHash = null;
    let gitgraph = null;
    let commits = [];
    let commitTags = {};

    /**
     * Инициализация модуля
     * @param {string} id - UUID модуля
     */
    function init(id) {
        moduleId = id;
        loadCommitHistory();
    }

    /**
     * Загрузка истории коммитов и текущего HEAD параллельно,
     * рендеринг только после получения обоих ответов.
     */
    function loadCommitHistory() {
        showLoading();

        const commitsReq = $.ajax({ url: `/api/modules/${moduleId}/commits`, method: 'GET' });
        const headReq    = $.ajax({ url: `/api/modules/${moduleId}/git-head`, method: 'GET' });
        const tagsReq    = $.ajax({ url: `/api/modules/${moduleId}/git-tags`, method: 'GET' });

        $.when(commitsReq, headReq, tagsReq)
            .done(function(commitsResp, headResp, tagsResp) {
                commits           = commitsResp[0];
                currentCommitHash = (headResp[0] && headResp[0].head) || null;
                commitTags        = tagsResp[0] || {};
                // Если HEAD не определён, считаем первый коммит текущим
                if (!currentCommitHash && commits.length > 0) {
                    currentCommitHash = commits[0].hash;
                }
                renderGraph();
                renderCommitsTable();
                hideLoading();
            })
            .fail(function(xhr, status, error) {
                showError('Ошибка загрузки истории коммитов: ' + error);
            });
    }

    /**
     * Отображение индикатора загрузки
     */
    function showLoading() {
        $('#git-graph').html('<div class="loading">Загрузка истории коммитов...</div>');
    }

    /**
     * Скрытие индикатора загрузки
     */
    function hideLoading() {
        $('.loading').remove();
    }

    /**
     * Отображение сообщения об ошибке
     */
    function showError(message) {
        $('#git-graph').html(`<div class="error-message">${message}</div>`);
    }

    /**
     * Рендеринг графа коммитов с помощью GitGraph.js
     */
    function renderGraph() {
        if (commits.length === 0) {
            $('#git-graph').html('<div class="loading">Нет коммитов для отображения</div>');
            return;
        }

        // Инициализация GitGraph
        const graphContainer = document.getElementById('git-graph');
        graphContainer.innerHTML = '';

        const GitgraphJS = window.GitgraphJS;
        if (!GitgraphJS) {
            showError('Библиотека GitGraph.js не загружена. Пожалуйста, обновите страницу.');
            console.error('GitgraphJS not found in window object');
            return;
        }

        const gitgraph = GitgraphJS.createGitgraph(graphContainer, {
            orientation: 'vertical',
            template: GitgraphJS.TemplateName.Metro,
            mode: 'compact'
        });

        // Создаем master ветку
        const master = gitgraph.branch('master');

        // Добавляем коммиты в обратном порядке (от старых к новым)
        const reversedCommits = [...commits].reverse();

        reversedCommits.forEach((commit, index) => {
            const isCurrent = commit.hash === currentCommitHash;
            const commitData = master.commit({
                subject: commit.message,
                author: 'RoboFactory System <system@robofactory.local>',
                onClick: function() {
                    showCommitDetails(commit);
                }
            });

            // Если это текущий HEAD, добавляем тег
            if (isCurrent) {
                master.tag('HEAD');
            }
        });
    }

    /**
     * Обновление подсветки текущего коммита в таблице без перерисовки всего
     */
    function updateCurrentCommitDisplay() {
        $('#commits-tbody tr').removeClass('current');
        $(`#commits-tbody tr[data-hash="${currentCommitHash}"]`).addClass('current');
    }

    /**
     * Отображение деталей коммита
     */
    function showCommitDetails(commit) {
        $('#commit-details').show();
        $('#commit-hash').text(commit.hash);
        $('#commit-message').text(commit.message);
        $('#commit-date').text(formatDate(commit.date));

        const checkoutBtn = $('#checkout-btn');
        checkoutBtn.prop('disabled', false);
        checkoutBtn.off('click').on('click', function() {
            performCheckout(commit.hash);
        });

        // Скрываем статус
        $('#checkout-status').removeClass('success error').text('');
    }

    /**
     * Форматирование даты
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Рендеринг таблицы коммитов
     */
    function renderCommitsTable() {
        const tbody = $('#commits-tbody');
        tbody.empty();

        commits.forEach(function(commit) {
            const isCurrent = commit.hash === currentCommitHash;
            const row = $('<tr>')
                .attr('data-hash', commit.hash)
                .toggleClass('current', isCurrent);

            row.append($('<td class="commit-hash-cell">').text(commit.hash.substring(0, 8)));
            row.append($('<td>').text(commit.message));
            row.append($('<td class="commit-date-cell">').text(formatDate(commit.date)));

            const tagsCell = $('<td class="commit-tags-cell">');
            const tags = commitTags[commit.hash] || [];
            tags.forEach(function(tag) {
                tagsCell.append(
                    $('<span class="commit-tag-badge">').text(tag)
                );
            });
            row.append(tagsCell);

            const actionsCell = $('<td>');
            if (isCurrent) {
                actionsCell.append($('<span class="current-badge">Текущая</span>'));
            } else {
                const checkoutBtn = $('<button class="checkout-btn-small">')
                    .text('Checkout')
                    .on('click', function() {
                        performCheckout(commit.hash);
                    });
                actionsCell.append(checkoutBtn);
            }

            row.append(actionsCell);
            tbody.append(row);
        });
    }

    /**
     * Выполнение checkout на указанный коммит
     * @param {string} commitHash
     * @param {boolean} force - сбросить незакоммиченные изменения перед checkout
     */
    function performCheckout(commitHash, force) {
        const statusDiv = $('#checkout-status');
        statusDiv.removeClass('success error').text('Выполняется checkout...');

        $('.checkout-button, .checkout-btn-small').prop('disabled', true);

        $.ajax({
            url: `/api/modules/${moduleId}/checkout`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ commit_hash: commitHash, force: !!force }),
            success: function(response) {
                statusDiv
                    .removeClass('error')
                    .addClass('success')
                    .text('✓ ' + response.message);

                currentCommitHash = commitHash;
                updateCurrentCommitDisplay();
                renderCommitsTable();
                renderGraph();
            },
            error: function(xhr) {
                if (xhr.status === 409) {
                    const confirmed = window.confirm(
                        'В рабочей директории есть незакоммиченные изменения.\n\n' +
                        'Они будут сброшены (git checkout -- .). Продолжить?'
                    );
                    if (confirmed) {
                        statusDiv.removeClass('success error').text('');
                        performCheckout(commitHash, true);
                        return;
                    }
                    statusDiv.removeClass('success error').text('');
                } else {
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.detail : 'Неизвестная ошибка';
                    statusDiv
                        .removeClass('success')
                        .addClass('error')
                        .text('✗ Ошибка: ' + errorMsg);
                }
            },
            complete: function() {
                $('.checkout-button, .checkout-btn-small').prop('disabled', false);
            }
        });
    }

    // Публичный API
    return {
        init: init
    };
})();

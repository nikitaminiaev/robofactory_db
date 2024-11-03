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
            detailsHtml += `<li><a href="/basic_object/${child}">${child}</a></li>`;
        });
        detailsHtml += '</ul>';
    }

    if (data.parents && data.parents.length > 0) {
        detailsHtml += '<h2>Parents</h2><ul>';
        data.parents.forEach(parent => {
            detailsHtml += `<li><a href="/basic_object/${parent}">${parent}</a></li>`;
        });
        detailsHtml += '</ul>';
    }

    return detailsHtml;
}
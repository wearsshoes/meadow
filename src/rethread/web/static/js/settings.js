function saveSettings(form) {
    const formData = new FormData(form);
    fetch('/settings', {
        method: 'POST',
        body: formData
    }).then(() => {
        document.getElementById('save-status').textContent = 'Changes saved';
        setTimeout(() => {
            document.getElementById('save-status').textContent = '';
        }, 2000);
    })
    .catch(() => {
        button.disabled = false;
    });
}

// Set initial paths for directory pickers
const screenshotInput = document.querySelector('input[name="screenshot_dir"]');
const notesInput = document.querySelector('input[name="notes_dir"]');

document.getElementById('screenshot_dir_picker').addEventListener('click', function(e) {
    // Use the current saved path from the input
    const currentPath = document.querySelector('input[name="screenshot_dir"]').value;
    e.target.setAttribute('nwworkingdir', currentPath);
});

document.getElementById('screenshot_dir_picker').addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        screenshotInput.value = e.target.files[0].path;
        saveSettings(screenshotInput.form);
    }
});

document.getElementById('notes_dir_picker').addEventListener('click', function(e) {
    // Use the current saved path from the input
    const currentPath = document.querySelector('input[name="notes_dir"]').value;
    e.target.setAttribute('nwworkingdir', currentPath);
});

document.getElementById('notes_dir_picker').addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        notesInput.value = e.target.files[0].path;
        saveSettings(notesInput.form);
    }
});

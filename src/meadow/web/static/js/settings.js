function saveSettings(form) {
    const formData = new FormData(form);
    fetch('/settings', {
        method: 'POST',
        body: formData
    }).then(() => {
        const status = document.getElementById('save-status');
        status.classList.add('show');
        setTimeout(() => {
            status.classList.remove('show');
        }, 2000);
    })
    .catch(() => {
        const status = document.getElementById('save-status');
        status.textContent = '❌ Error saving changes';
        status.style.background = '#f44336';
        status.classList.add('show');
        setTimeout(() => {
            status.classList.remove('show');
        }, 2000);
    });
}
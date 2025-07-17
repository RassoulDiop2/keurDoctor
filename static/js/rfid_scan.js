document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.scan-rfid-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const fieldName = btn.getAttribute('data-field');
            btn.disabled = true;
            btn.textContent = "En attente...";
            fetch('/admin/scan-rfid-uid/')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.querySelector(`[name="${fieldName}"]`).value = data.uid;
                        btn.textContent = "Scanner";
                        alert("UID détecté : " + data.uid);
                    } else {
                        btn.textContent = "Scanner";
                        alert("Erreur : " + data.error);
                    }
                    btn.disabled = false;
                })
                .catch(err => {
                    btn.textContent = "Scanner";
                    btn.disabled = false;
                    alert("Erreur de communication");
                });
        });
    });
}); 
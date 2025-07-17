document.addEventListener('DOMContentLoaded', function () {
    // Fonction pour créer un bouton de scan RFID
    function createScanButton(fieldId, fieldType) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Créer le bouton
        const scanBtn = document.createElement('button');
        scanBtn.type = 'button';
        scanBtn.className = 'btn btn-primary btn-sm scan-rfid-btn';
        scanBtn.textContent = 'Scanner ' + fieldType;
        scanBtn.style.marginLeft = '10px';

        // Ajouter l'événement de clic
        scanBtn.addEventListener('click', function () {
            scanRFID(field, scanBtn, fieldType);
        });

        // Insérer le bouton après le champ
        field.parentNode.insertBefore(scanBtn, field.nextSibling);
    }

    // Fonction pour scanner RFID
    function scanRFID(field, button, fieldType) {
        button.disabled = true;
        button.textContent = 'En attente...';

        fetch('/administration/scan-rfid/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    field.value = data.uid;
                    button.textContent = 'Scanner ' + fieldType;
                    showAlert('success', `${fieldType} détecté : ${data.uid}`);
                } else {
                    button.textContent = 'Scanner ' + fieldType;
                    showAlert('error', 'Erreur : ' + data.error);
                }
                button.disabled = false;
            })
            .catch(err => {
                button.textContent = 'Scanner ' + fieldType;
                button.disabled = false;
                showAlert('error', 'Erreur de communication avec le serveur');
            });
    }

    // Fonction pour afficher des alertes
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insérer l'alerte en haut du formulaire
        const form = document.querySelector('form');
        if (form) {
            form.parentNode.insertBefore(alertDiv, form);

            // Auto-supprimer après 5 secondes
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    // Créer les boutons de scan pour les champs RFID
    createScanButton('id_rfid_uid', 'Carte RFID');
    createScanButton('id_badge_bleu_uid', 'Badge Bleu');

    // Ajouter des styles CSS
    const style = document.createElement('style');
    style.textContent = `
        .scan-rfid-btn {
            background-color: #007bff;
            border-color: #007bff;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }
        .scan-rfid-btn:hover {
            background-color: #0056b3;
            border-color: #0056b3;
        }
        .scan-rfid-btn:disabled {
            background-color: #6c757d;
            border-color: #6c757d;
            cursor: not-allowed;
        }
    `;
    document.head.appendChild(style);
}); 
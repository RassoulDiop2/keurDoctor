<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>KeurDoctorSecure - Connexion</title>
    <link rel="stylesheet" href="resources/css/keurdoctor.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body class="kd-bg-gradient">
    <div class="kd-login-container">
        <div class="kd-login-card">
            <img src="resources/img/logo.png" alt="KeurDoctor Logo" class="kd-logo">
            <h1 class="kd-title">KEURDOCTORSECURE</h1>
            <p class="kd-slogan">Votre santé, notre priorité</p>

            <#-- Affichage des erreurs Keycloak -->
            <#if message?has_content>
                <div class="kd-error">${message.summary}</div>
            </#if>

            <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post">
                <div class="kd-input-group">
                    <span class="kd-input-icon"><i class="fas fa-user"></i></span>
                    <input tabindex="1" id="username" class="kd-input" name="username" value="${(login.username!'')}" type="text" autofocus autocomplete="username" placeholder="Nom d'utilisateur ou email" required>
                </div>
                <div class="kd-input-group">
                    <span class="kd-input-icon"><i class="fas fa-lock"></i></span>
                    <input tabindex="2" id="password" class="kd-input" name="password" type="password" autocomplete="current-password" placeholder="Mot de passe" required>
                    <span class="kd-input-icon kd-toggle-password" onclick="togglePassword()"><i id="eye-icon" class="fas fa-eye"></i></span>
                </div>
                <div class="kd-actions">
                    <button type="submit" id="kc-login" class="kd-btn kd-btn-primary">Se connecter</button>
                </div>
                <div class="kd-links">
                    <a href="${url.loginResetCredentialsUrl}" class="kd-link">Mot de passe oublié ?</a>
                </div>
            </form>
        </div>
    </div>
    <footer class="kd-footer">
        &copy; ${.now?string("yyyy")} KeurDoctor. Tous droits réservés.
    </footer>
    <script src="https://kit.fontawesome.com/4b8b0b6b2a.js" crossorigin="anonymous"></script>
    <script>
        function togglePassword() {
            var pwd = document.getElementById('password');
            var icon = document.getElementById('eye-icon');
            if (pwd.type === 'password') {
                pwd.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                pwd.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }
    </script>
</body>
</html> 
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('password','password-confirm') displayInfo=false; section>
    <#if section = "header">
        <p id="kc-page-title">${msg("updatePasswordTitle")}</p>
    <#elseif section = "form">
        <form id="kc-passwd-update-form" action="${url.loginAction}" method="post">
            <input type="text" id="username" name="username" value="${username}" autocomplete="username" readonly="readonly" style="display:none;"/>
            <input type="password" id="password" name="password" autocomplete="current-password" style="display:none;"/>

            <div class="form-group">
                <label for="password-new" class="sr-only">${msg("passwordNew")}</label>
                <div class="password-wrapper">
                    <input type="password" id="password-new" name="password-new" class="form-control" autofocus autocomplete="new-password"
                           aria-invalid="<#if messagesPerField.existsError('password','password-confirm')>true</#if>"
                           placeholder="${msg("passwordNew")}"
                           required />
                    <span id="toggle-password-new" class="password-toggle-icon" role="button" title="Afficher/Masquer le mot de passe">
                        <svg id="eye-icon-open-new" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        <svg id="eye-icon-closed-new" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                    </span>
                </div>
                <#if messagesPerField.existsError('password')>
                    <span id="input-error-password" class="kc-feedback-text" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('password'))?no_esc}
                    </span>
                </#if>
            </div>

            <div class="form-group">
                <label for="password-confirm" class="sr-only">${msg("passwordConfirm")}</label>
                <div class="password-wrapper">
                    <input type="password" id="password-confirm" name="password-confirm" class="form-control" autocomplete="new-password"
                           aria-invalid="<#if messagesPerField.existsError('password-confirm')>true</#if>"
                           placeholder="${msg("passwordConfirm")}"
                           required />
                    <span id="toggle-password-confirm" class="password-toggle-icon" role="button" title="Afficher/Masquer le mot de passe">
                        <svg id="eye-icon-open-confirm" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        <svg id="eye-icon-closed-confirm" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                    </span>
                </div>
                <#if messagesPerField.existsError('password-confirm')>
                    <span id="input-error-password-confirm" class="kc-feedback-text" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('password-confirm'))?no_esc}
                    </span>
                </#if>
            </div>

            <div class="form-group">
                <#if isAppInitiatedAction??>
                    <input class="btn btn-primary" type="submit" value="${msg("doSubmit")}" />
                    <button class="btn btn-secondary" type="submit" name="cancel-aia" value="true" />${msg("doCancel")}</button>
                <#else>
                    <input class="btn btn-primary btn-block" type="submit" value="${msg("doSubmit")}" />
                </#if>
            </div>
        </form>

        <script>
            function togglePasswordVisibility(passwordFieldId, openIconId, closedIconId) {
                const passwordField = document.getElementById(passwordFieldId);
                const eyeIconOpen = document.getElementById(openIconId);
                const eyeIconClosed = document.getElementById(closedIconId);

                if (passwordField.type === 'password') {
                    passwordField.type = 'text';
                    if(eyeIconOpen) eyeIconOpen.style.display = 'none';
                    if(eyeIconClosed) eyeIconClosed.style.display = 'block';
                } else {
                    passwordField.type = 'password';
                    if(eyeIconOpen) eyeIconOpen.style.display = 'block';
                    if(eyeIconClosed) eyeIconClosed.style.display = 'none';
                }
            }

            document.getElementById('toggle-password-new')?.addEventListener('click', function() {
                togglePasswordVisibility('password-new', 'eye-icon-open-new', 'eye-icon-closed-new');
            });

            document.getElementById('toggle-password-confirm')?.addEventListener('click', function() {
                togglePasswordVisibility('password-confirm', 'eye-icon-open-confirm', 'eye-icon-closed-confirm');
            });

            document.getElementById('password-confirm').addEventListener('input', function() {
                var password = document.getElementById('password-new').value;
                var passwordConfirm = this.value;
                
                if (password !== passwordConfirm) {
                    this.setCustomValidity('Les mots de passe ne correspondent pas');
                } else {
                    this.setCustomValidity('');
                }
            });
        </script>
    </#if>
</@layout.registrationLayout>

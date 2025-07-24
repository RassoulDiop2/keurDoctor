<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password') displayInfo=realm.password && realm.registrationAllowed && !registrationDisabled??; section>
    <#if section = "header">
        <h2>
            <#if realm.displayName?has_content>
                ${msg("loginAccountTitle")}
            <#else>
                ${msg("loginTitle")}
            </#if>
        </h2>
    <#elseif section = "form">
        <div id="kc-form">
            <div id="kc-form-wrapper">
                <#if realm.password>
                    <form id="kc-form-login" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post" class="space-y-6">
                        <div class="rounded-md shadow-sm space-y-4">
                            <div class="form-group">
                                <label for="username" class="sr-only">
                                    <#if !realm.loginWithEmailAllowed>
                                        ${msg("username")}
                                    <#elseif !realm.registrationEmailAsUsername>
                                        ${msg("usernameOrEmail")}
                                    <#else>
                                        ${msg("email")}
                                    </#if>
                                </label>

                                <#if usernameEditDisabled??>
                                    <input tabindex="1" id="username" name="username" value="${(login.username!'')}" type="text" disabled 
                                           placeholder="<#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>Nom d'utilisateur ou email<#else>Adresse email</#if>" />
                                <#else>
                                    <input tabindex="1" id="username" name="username" value="${(login.username!'')}" type="text" autofocus autocomplete="username"
                                           aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                           placeholder="<#if !realm.loginWithEmailAllowed>Nom d'utilisateur<#elseif !realm.registrationEmailAsUsername>Nom d'utilisateur ou email<#else>Adresse email</#if>"
                                           required />
                                </#if>

                                <#if messagesPerField.existsError('username','password')>
                                    <span id="input-error-username" aria-live="polite">
                                        ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                                    </span>
                                </#if>
                            </div>

                            <div class="form-group">
                                <label for="password" class="sr-only">${msg("password")}</label>
                                <div class="password-wrapper">
                                    <input tabindex="2" id="password" name="password" type="password" autocomplete="current-password"
                                           aria-invalid="<#if messagesPerField.existsError('username','password')>true</#if>"
                                           placeholder="Mot de passe"
                                           required />
                                    <span id="toggle-password" class="password-toggle-icon" role="button" title="Afficher/Masquer le mot de passe">
                                        <svg id="eye-icon-open" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                        <svg id="eye-icon-closed" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                                    </span>
                                </div>
                            </div>
                        </div>

                        <#if realm.rememberMe && !usernameEditDisabled??>
                            <div class="form-group-checkbox">
                                <div class="checkbox">
                                    <#if login.rememberMe??>
                                        <input tabindex="3" id="rememberMe" name="rememberMe" type="checkbox" checked> 
                                        <label for="rememberMe">Se souvenir de moi</label>
                                    <#else>
                                        <input tabindex="3" id="rememberMe" name="rememberMe" type="checkbox"> 
                                        <label for="rememberMe">Se souvenir de moi</label>
                                    </#if>
                                </div>
                            </div>
                        </#if>

                        <#if realm.resetPasswordAllowed>
                            <div class="kc-form-options">
                                <a tabindex="5" href="http://localhost:8080/realms/KeurDoctorSecure/login-actions/reset-credentials?client_id=django-KDclient">Mot de passe oublié?</a>
                            </div>
                        </#if>

                        <div class="form-group">
                            <div id="kc-form-buttons">
                                <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                                <button tabindex="4" name="login" id="kc-login" type="submit">
                                    <span id="button-text">Se connecter</span>
                                    <svg id="loading-spinner" style="display: none; animation: spin 1s linear infinite; margin-left: 8px;" width="16" height="16" viewBox="0 0 24 24" fill="none">
                                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" opacity="0.25"></circle>
                                        <path fill="currentColor" opacity="0.75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </form>

                    <script>
                        // Toggle password visibility
                        document.getElementById('toggle-password')?.addEventListener('click', function() {
                            const passwordField = document.getElementById('password');
                            const eyeIconOpen = document.getElementById('eye-icon-open');
                            const eyeIconClosed = document.getElementById('eye-icon-closed');
                            
                            if (passwordField.type === 'password') {
                                passwordField.type = 'text';
                                if(eyeIconOpen) eyeIconOpen.style.display = 'none';
                                if(eyeIconClosed) eyeIconClosed.style.display = 'block';
                            } else {
                                passwordField.type = 'password';
                                if(eyeIconOpen) eyeIconOpen.style.display = 'block';
                                if(eyeIconClosed) eyeIconClosed.style.display = 'none';
                            }
                        });

                        // Loading state for submit button
                        document.getElementById('kc-form-login')?.addEventListener('submit', function() {
                            const button = document.getElementById('kc-login');
                            const buttonText = document.getElementById('button-text');
                            const spinner = document.getElementById('loading-spinner');
                            
                            if(button) {
                                button.disabled = true;
                                button.style.opacity = '0.75';
                                button.style.cursor = 'not-allowed';
                            }
                            if(buttonText) buttonText.textContent = 'Connexion en cours...';
                            if(spinner) spinner.style.display = 'inline-block';
                        });

                        // Add keyframes for spinner
                        const style = document.createElement('style');
                        style.textContent = `
                            @keyframes spin {
                                from { transform: rotate(0deg); }
                                to { transform: rotate(360deg); }
                            }
                        `;
                        document.head.appendChild(style);
                    </script>
                </#if>

                <#-- Social providers removed as requested -->
                <#-- 
                <#if realm.password && social.providers??>
                    <div id="kc-social-providers" style="margin-top: 32px;">
                        <div style="text-align: center; margin: 24px 0; position: relative;">
                            <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: var(--gray-300);"></div>
                            <span style="background: white; padding: 0 16px; color: var(--gray-500); font-size: 14px;">Ou continuer avec</span>
                        </div>

                        <div style="display: grid; gap: 12px;">
                            <#list social.providers as p>
                                <a id="social-${p.alias}" href="${p.loginUrl}" 
                                   style="display: flex; align-items: center; justify-content: center; padding: 8px 16px; border: 1px solid var(--gray-300); border-radius: 6px; text-decoration: none; color: var(--gray-700); font-weight: 500; transition: all 0.2s; background: white;"
                                   onmouseover="this.style.backgroundColor='var(--gray-50)'" 
                                   onmouseout="this.style.backgroundColor='white'">
                                    <#if p.iconClasses?has_content>
                                        <i class="${p.iconClasses}" style="margin-right: 8px;" aria-hidden="true"></i>
                                    </#if>
                                    <span>${p.displayName!}</span>
                                </a>
                            </#list>
                        </div>
                    </div>
                </#if>
                -->
            </div>
        </div>
    <#elseif section = "info" >
        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
            <div id="kc-registration-container">
                <div id="kc-registration">
                    <span>${msg("noAccount")} <a tabindex="6" href="${url.registrationUrl}">${msg("doRegister")}</a></span>
                </div>
            </div>
        </#if>
    </#if>
</@layout.registrationLayout>

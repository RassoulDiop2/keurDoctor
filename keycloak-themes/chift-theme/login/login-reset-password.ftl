<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username') displayInfo=false; section>
    <#if section = "header">
        <p id="kc-page-title">${msg("emailForgotTitle")}</p>
    <#elseif section = "form">
        <form id="kc-reset-password-form" action="${url.loginAction}" method="post">
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
                <input type="text" id="username" name="username" class="form-control" autofocus 
                       value="${(auth.attemptedUsername!'')}" 
                       aria-invalid="<#if messagesPerField.existsError('username')>true</#if>"
                       placeholder="<#if !realm.loginWithEmailAllowed>Nom d'utilisateur<#elseif !realm.registrationEmailAsUsername>Nom d'utilisateur ou email<#else>Adresse email</#if>"
                       required />
                <#if messagesPerField.existsError('username')>
                    <span id="input-error-username" class="kc-feedback-text" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('username'))?no_esc}
                    </span>
                </#if>
            </div>
            
            <div class="form-group">
                <input class="btn btn-primary btn-block" type="submit" value="${msg("doSubmit")}"/>
            </div>
            
            <div class="kc-form-options" style="text-align: center; margin-top: 1.5rem;">
                <a href="${url.loginUrl}">← ${msg("backToLogin")}</a>
            </div>
        </form>
    </#if>
</@layout.registrationLayout>

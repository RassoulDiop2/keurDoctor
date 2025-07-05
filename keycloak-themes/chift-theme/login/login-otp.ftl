<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('totp') displayInfo=false; section>
    <#if section = "header">
        <h2 id="kc-page-title">${msg("loginOtpTitle")}</h2>
        <p class="instruction">
            ${msg("loginOtpOneTime.instruction")}
        </p>
    <#elseif section = "form">
        <form id="kc-otp-login-form" action="${url.loginAction}" method="post">
            <#if otpLogin.userOtpCredentials?size gt 1>
                <div class="form-group">
                    <div class="select-auth-box-headline">
                        ${msg("loginChooseAuthenticator")}
                    </div>
                    <div class="select-auth-box-list">
                        <#list otpLogin.userOtpCredentials as otpCredential>
                            <input id="kc-otp-credential-${otpCredential?index}" class="select-auth-box-list-item" type="radio" name="selectedCredentialId" value="${otpCredential.id}" <#if otpCredential.id == otpLogin.selectedCredentialId>checked="checked"</#if>>
                            <label for="kc-otp-credential-${otpCredential?index}" class="select-auth-box-list-item-label">
                                <span class="select-auth-box-list-item-title">${otpCredential.userLabel}</span>
                                <span class="select-auth-box-list-item-description">
                                    <#if otpCredential.type == "totp">
                                        ${msg("loginOtpType.totp")}
                                    <#elseif otpCredential.type == "hotp">
                                        ${msg("loginOtpType.hotp")}
                                    </#if>
                                </span>
                            </label>
                        </#list>
                    </div>
                </div>
            </#if>

            <div class="form-group">
                <label for="otp" class="sr-only">${msg("loginOtpOneTime")}</label>
                <input id="otp" name="otp" autocomplete="off" type="text" class="form-control" maxlength="6" minlength="6" 
                       autofocus aria-invalid="<#if messagesPerField.existsError('totp')>true</#if>"
                       placeholder="000000"/>

                <#if messagesPerField.existsError('totp')>
                    <span id="input-error-otp-code" class="kc-feedback-text" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('totp'))?no_esc}
                    </span>
                </#if>
            </div>

            <div class="form-group">
                <input class="btn btn-primary btn-block" name="login" id="kc-login" type="submit" value="${msg("doLogIn")}"/>
            </div>

            <#if auth?has_content && auth.showTryAnotherWayLink()>
                <div class="kc-form-options" style="text-align: center; margin-top: 1.5rem;">
                    <a href="#" onclick="document.forms['kc-select-try-another-way-form'].submit();return false;">${msg("doTryAnotherWay")}</a>
                </div>
                <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post" style="display: none;">
                    <input type="hidden" name="tryAnotherWay" value="on"/>
                </form>
            </#if>
        </form>

        <script>
            document.getElementById('otp')?.addEventListener('input', function(e) {
                this.value = this.value.replace(/[^0-9]/g, '');
                if (this.value.length > 6) {
                    this.value = this.value.substr(0, 6);
                }
                if (this.value.length === 6) {
                    document.getElementById('kc-otp-login-form').submit();
                }
            });

            document.getElementById('otp')?.addEventListener('paste', function(e) {
                e.preventDefault();
                const paste = (e.clipboardData || window.clipboardData).getData('text');
                const numericPaste = paste.replace(/[^0-9]/g, '').substr(0, 6);
                this.value = numericPaste;
                if (numericPaste.length === 6) {
                    document.getElementById('kc-otp-login-form').submit();
                }
            });
        </script>
    </#if>
</@layout.registrationLayout>

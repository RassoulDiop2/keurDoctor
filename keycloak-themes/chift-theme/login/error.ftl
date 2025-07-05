<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        <#-- The title is already handled by the alert message, so we can leave this empty -->
    <#elseif section = "form">
        <div id="kc-error-message" class="text-center">
            <h2 id="kc-page-title" class="text-2xl font-bold mb-4">
                <#if message.type == 'error'>
                    ${msg("errorTitle")}
                <#elseif message.type == 'warning'>
                    ${msg("warningTitle")}
                <#else>
                    ${msg("pageNotFound")}
                </#if>
            </h2>

            <div class="alert alert-${message.type!'info'} mb-6">
                <p>${kcSanitize(message.summary)?no_esc}</p>
            </div>

            <div class="space-y-4">
                <#if client?? && client.baseUrl?has_content>
                    <a href="${client.baseUrl}" class="btn btn-primary btn-block">
                        ${msg("backToApplication")}
                    </a>
                </#if>
                <a href="${url.loginUrl}" class="btn btn-secondary btn-block">
                    ${msg("backToLogin")}
                </a>
            </div>

            <#if skipLink??>
                <div class="mt-6">
                    <a href="${skipLink.uri}">${kcSanitize(skipLink.text)?no_esc}</a>
                </div>
            </#if>
        </div>
    </#if>
</@layout.registrationLayout>

<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>
    <#if section = "header">
        <h2 id="kc-page-title">${msg("emailVerifyTitle")}</h2>
    <#elseif section = "form">
        <div class="verify-email-container">
            <div class="verify-email-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-green-500">
                    <circle cx="12" cy="12" r="11" fill="#ECFDF5"/>
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
            </div>

            <p class="instruction">
                ${msg("emailVerifyInstruction1", user.email)}
            </p>

            <div class="email-address">
                ${user.email}
            </div>

            <p class="instruction-secondary">
                ${msg("emailVerifyInstruction2")} <a href="${url.loginAction}">${msg("doClickHere")}</a> ${msg("emailVerifyInstruction3")}
            </p>

            <div class="mt-8">
                <form id="kc-form-logout" action="${url.logoutUrl}" method="post">
                    <input class="btn btn-secondary btn-block" type="submit" value="${msg("doLogOut")}" />
                </form>
            </div>
        </div>

        <script>
            // Optional: Add a script to resend email without leaving the page.
            // This is a basic example.
            document.querySelector('.resend-email a')?.addEventListener('click', function(e) {
                e.preventDefault();
                // You might want to add a loading indicator here
                fetch(this.href, { method: 'GET' })
                    .then(response => {
                        // Handle success/error message display
                    });
            });
        </script>
    </#if>
</@layout.registrationLayout>

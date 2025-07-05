<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false showAnotherWayIfPresent=true>
<!DOCTYPE html>
<html class="${(realm.internationalizationEnabled)?then('true','false')}">

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <#if properties.meta?has_content>
        <#list properties.meta?split(' ') as meta>
            <meta name="${meta?split('==')[0]}" content="${meta?split('==')[1]}"/>
        </#list>
    </#if>
    
    <title>${msg("loginTitle",(realm.displayName!''))}</title>
    
    <link rel="icon" href="${url.resourcesPath}/img/favicon.ico" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${url.resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.scripts?has_content>
        <#list properties.scripts?split(' ') as script>
            <script src="${url.resourcesPath}/${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
        </#list>
    </#if>
    
    <!-- Design CHIFT moderne, responsive et centré -->
    <style>
        /* Variables CSS CHIFT */
        :root {
          --chift-blue: #0E6B85;
          --chift-light-blue: #037ea0;
          --chift-light-blue-2: #0491b8;
          --gray-50: #F9FAFB;
          --gray-100: #F3F4F6;
          --gray-200: #E5E7EB;
          --gray-300: #D1D5DB;
          --gray-400: #9CA3AF;
          --gray-500: #6B7280;
          --gray-600: #475569;
          --gray-700: #374151;
          --gray-800: #1F2937;
          --gray-900: #111827;
          --white: #FFFFFF;
          --red-500: #EF4444;
          --red-50: #FEF2F2;
          --green-500: #10B981;
          --green-50: #ECFDF5;
        }

        /* Reset global */
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        html, body {
          height: 100%;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background-color: var(--gray-50);
          color: var(--gray-900);
        }

        /* Structure principale - Flexbox pour centrage */
        body {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
        }

        /* Container principal centré */
        .login-pf-page {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem 1rem;
          background-color: var(--gray-50);
        }

        /* Carte de connexion responsive */
        .card-pf {
          width: 100%;
          max-width: 28rem;
          background: var(--white);
          border:none;
          border-radius: 0.75rem;
          box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.05);
          padding: 2.5rem;
        }

        /* Header avec logo */
        .login-pf-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .logo-container {
          margin-bottom: 1.5rem;
        }

        .logo-container img {
          height: 3.5rem;
          width: auto;
          max-width: 100%;
          object-fit: contain;
        }

        /* Titres */
        h1, h2 {
          color: var(--chift-blue);
          font-size: 1.5rem;
          font-weight: 600;
          text-align: center;
          margin-bottom: 1.5rem;
          line-height: 1.25;
        }

        #kc-page-title {
        color: var(--chift-blue);
        font-size: 1rem;         /* ≈ 8px pour les petits écrans */
        font-weight: 400;
        text-align: center;
        margin-bottom: 1.5rem;
        line-height: 1;
        word-break: break-word;
        white-space: normal;
        padding: 0 0.25rem;
        }

        /* Taille intermédiaire : petits téléphones larges */
        @media (min-width: 360px) {
        #kc-page-title {
            font-size: 0.75rem;
        }
        }

        /* Taille moyenne : téléphones plus larges */
        @media (min-width: 480px) {
        #kc-page-title {
            font-size: 0.75rem;
        }
        }

        /* Tablettes et + */
        @media (min-width: 768px) {
        #kc-page-title {
            font-size: 0.875rem;
        }
        }





        /* Messages d'alerte */
        .alert {
          padding: 0.875rem 1rem;
          border-radius: 0.5rem;
          margin-bottom: 1.5rem;
          border: 1px solid;
          font-size: 0.875rem;
          line-height: 1.5;
        }

        .alert-error {
          background-color: var(--red-50);
          color: var(--red-500);
          border-color: var(--red-500);
        }

        .alert-success {
          background-color: var(--green-50);
          color: var(--green-500);
          border-color: var(--green-500);
        }

        .alert-warning {
          background-color: #FEF3C7;
          color: #D97706;
          border-color: #D97706;
        }

        .alert-info {
          background-color: #EBF8FF;
          color: var(--chift-blue);
          border-color: var(--chift-blue);
        }

        /* Formulaires */
        #kc-form {
          width: 100%;
        }

        .form-group {
          margin-bottom: 1.25rem;
        }

        /* Labels */
        label {
          display: block;
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--gray-700);
          margin-bottom: 0.5rem;
        }

        /* Labels cachés pour accessibilité */
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0,0,0,0);
          white-space: nowrap;
          border: 0;
        }

        /* Inputs */
        .password-wrapper {
          position: relative;
        }

        input[type="text"],
        input[type="email"],
        input[type="password"],
        input[type="tel"] {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 1px solid var(--gray-300);
          border-radius: 0.5rem;
          font-size: 1rem;
          line-height: 1.5;
          background-color: var(--white);
          color: var(--gray-900);
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .password-toggle-icon {
            position: absolute;
            top: 50%;
            right: 1rem;
            transform: translateY(-50%);
            cursor: pointer;
            color: var(--gray-500);
            width: 1.25rem;
            height: 1.25rem;
        }
        
        input[type="password"] {
            padding-right: 3rem; 
        }

        input[type="text"]:focus,
        input[type="email"]:focus,
        input[type="password"]:focus,
        input[type="tel"]:focus {
          outline: none;
          border-color: var(--chift-blue);
          box-shadow: 0 0 0 3px rgba(14, 107, 133, 0.1);
        }

        input::placeholder {
          color: var(--gray-400);
        }

        /* Inputs avec erreur */
        .has-error input,
        input[aria-invalid="true"] {
          border-color: var(--red-500);
          box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
        }

        /* Messages d'erreur */
        .kc-feedback-text,
        #input-error,
        #input-error-username,
        #input-error-password,
        span[id^="input-error"] {
          color: var(--red-500);
          font-size: 0.875rem;
          margin-top: 0.25rem;
          display: block;
        }

        /* Boutons */
        .btn,
        input[type="submit"],
        button[type="submit"] {
          width: 100%;
          padding: 0.875rem 1.5rem;
          background-color: var(--chift-blue);
          color: var(--white);
          border: 1px solid var(--chift-blue);
          border-radius: 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s, color 0.2s;
          text-align: center;
          text-decoration: none;
          display: inline-block;
        }

        .btn:hover,
        input[type="submit"]:hover,
        button[type="submit"]:hover {
          background-color: var(--chift-light-blue);
          color: var(--white);
        }

        .btn:focus,
        input[type="submit"]:focus,
        button[type="submit"]:focus {
          outline: none;
          box-shadow: 0 0 0 3px rgba(14, 107, 133, 0.2);
        }

        .btn:disabled,
        input[type="submit"]:disabled,
        button[type="submit"]:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Liens */
        a {
          color: var(--chift-blue);
          text-decoration: none;
          font-weight: 500;
        }

        a:hover {
          color: var(--chift-light-blue);
          text-decoration: underline;
        }

        /* Options de formulaire */
        .kc-form-options {
          text-align: right;
          margin-bottom: 1.5rem;
        }

        .kc-form-options a {
          font-size: 0.875rem;
        }

        /* Checkbox */
        .checkbox {
          display: flex;
          align-items: center;
          margin: 1rem 0;
        }

        .checkbox input[type="checkbox"] {
          width: 1rem;
          height: 1rem;
          margin-right: 0.5rem;
          margin-bottom: 0;
          accent-color: var(--chift-blue);
        }

        .checkbox label {
          margin: 0;
          font-size: 0.875rem;
          font-weight: 400;
        }

        /* Footer */
        .kc-footer {
          background-color: var(--white);
          border-top: 1px solid var(--gray-200);
          padding: 1rem;
          text-align: center;
          color: var(--gray-500);
          font-size: 0.875rem;
        }

        .kc-footer p {
          margin: 0;
        }

        /* Responsive Design */
        
        /* Mobile Portrait (jusqu'à 480px) */
        @media (max-width: 480px) {
          .login-pf-page {
            padding: 1rem 0.5rem;
          }
          
          .card-pf {
            padding: 2rem 1.5rem;
            border-radius: 0.5rem;
            max-width: 100%;
          }
          
          .logo-container img {
            height: 3rem;
          }
          
          h1, h2 {
            font-size: 1.25rem;
          }
          
          input[type="text"],
          input[type="email"],
          input[type="password"],
          input[type="tel"] {
            padding: 0.875rem;
            font-size: 1rem;
          }
          
          .btn,
          input[type="submit"],
          button[type="submit"] {
            padding: 1rem;
            font-size: 1rem;
          }
        }

        /* Mobile Landscape (481px - 640px) */
        @media (min-width: 481px) and (max-width: 640px) {
          .card-pf {
            max-width: 26rem;
            padding: 2.25rem;
          }
        }

        /* Tablet (641px - 1024px) */
        @media (min-width: 641px) and (max-width: 1024px) {
          .login-pf-page {
            padding: 2rem;
          }
          
          .card-pf {
            max-width: 30rem;
            padding: 2.5rem;
          }
        }

        /* Desktop (1025px et plus) */
        @media (min-width: 1025px) {
          .login-pf-page {
            padding: 3rem;
          }
          
          .card-pf {
            max-width: 32rem;
            padding: 3rem;
          }
        }

        /* Corrections spécifiques Keycloak */
        .login-pf-page .card-pf .login-pf-header {
          margin-bottom: 2rem;
        }

        #kc-content {
          width: 100%;
        }

        #kc-content-wrapper {
          width: 100%;
        }

        .login-pf-brand {
          display: none;
        }

        /* Espacement des groupes */
        .form-group:last-child {
          margin-bottom: 0;
        }

        /* Style pour "Try another way" */
        #try-another-way {
          font-size: 0.875rem;
          margin-top: 1rem;
          display: inline-block;
        }

        /* Info section */
        #kc-info {
          margin-top: 1.5rem;
          text-align: center;
        }

        #kc-info a {
          font-size: 0.875rem;
        }

        /* Masquer icônes Keycloak par défaut */
        .pficon {
          display: none;
        }

        /* OTP and Authenticator Selection */
        .instruction {
          background-color: var(--gray-100);
          border: 1px solid var(--gray-200);
          border-radius: 0.5rem;
          padding: 1rem;
          margin-bottom: 1.5rem;
          color: var(--gray-700);
          font-size: 0.875rem;
          text-align: center;
        }

        .select-auth-box-headline {
          font-weight: 600;
          margin-bottom: 1rem;
          color: var(--gray-800);
        }

        .select-auth-box-list {
          margin-bottom: 1.5rem;
        }

        .select-auth-box-list-item {
          display: none; /* Hide radio button */
        }

        .select-auth-box-list-item-label {
          display: block;
          padding: 1rem;
          border: 2px solid var(--gray-300);
          border-radius: 0.5rem;
          margin-bottom: 0.5rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .select-auth-box-list-item:checked + .select-auth-box-list-item-label {
          border-color: var(--chift-blue);
          background-color: #EBF8FF;
          box-shadow: 0 0 0 2px rgba(14, 107, 133, 0.1);
        }

        .select-auth-box-list-item-title {
          font-weight: 600;
          color: var(--gray-900);
          display: block;
        }

        .select-auth-box-list-item-description {
          font-size: 0.875rem;
          color: var(--gray-600);
        }

        #otp {
          text-align: center;
          font-size: 1.5rem;
          letter-spacing: 0.5rem;
          font-family: 'Courier New', monospace;
          padding-left: calc(1rem + 0.5rem); /* Adjust padding to center text with letter-spacing */
        }

        /* Email Verification Page */
        .verify-email-container {
          text-align: center;
        }

        .verify-email-icon {
          margin-bottom: 1.5rem;
        }

        .verify-email-icon svg {
            width: 4rem;
            height: 4rem;
        }

        .instruction-secondary {
          color: var(--gray-600);
          font-size: 0.875rem;
          line-height: 1.5;
          margin-bottom: 2rem;
        }

        .email-address {
          background-color: var(--gray-100);
          border: 1px solid var(--gray-200);
          border-radius: 0.5rem;
          padding: 1rem;
          margin: 1.5rem 0;
          font-family: 'Courier New', monospace;
          font-weight: 600;
          color: var(--chift-blue);
          word-break: break-all;
        }

        .resend-email {
          padding-top: 1rem;
          margin-top: 1rem;
          border-top: 1px solid var(--gray-200);
          font-size: 0.875rem;
          color: var(--gray-600);
          line-height: 1.5;
        }

        .resend-email a {
          font-weight: 600;
          text-decoration: underline;
        }
    </style>
</head>

<body class="${bodyClass}">
    <div class="login-pf-page">
        <div class="card-pf">
            <!--
            <div class="logo-container">
            <img src="${url.resourcesCommonPath}/images/logo_1.png" alt="CHIFT Logo" />
            </div>
            -->
            <div id="kc-content">
                <div id="kc-content-wrapper">
                    <#-- Messages d'alerte -->
                    <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                        <div class="alert alert-${message.type}">
                            <span class="kc-feedback-text">${kcSanitize(message.summary)?no_esc}</span>
                        </div>
                    </#if>

                    <#nested "header">

                    <div id="kc-form">
                        <div id="kc-form-wrapper">
                            <#nested "form">
                        </div>
                    </div>

                    <#if auth?has_content && auth.showTryAnotherWayLink() && showAnotherWayIfPresent>
                        <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post">
                            <div>
                                <input type="hidden" name="tryAnotherWay" value="on" />
                                <a href="#" id="try-another-way" onclick="document.forms['kc-select-try-another-way-form'].submit();return false;">${msg("doTryAnotherWay")}</a>
                            </div>
                        </form>
                    </#if>

                    <#if displayInfo>
                        <div id="kc-info">
                            <div id="kc-info-wrapper">
                                <#nested "info">
                            </div>
                        </div>
                    </#if>
                </div>
            </div>
        </div>
    </div>

    <footer class="kc-footer">
        <p>&copy; ${.now?string("yyyy")} Keur Doctor. Tous droits réservés.</p>
    </footer>
</body>
</html>
</#macro>

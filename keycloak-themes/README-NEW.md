# 🎨 Thème Keycloak CHIFT

Thème personnalisé moderne et responsive pour CHIFT, intégré avec Docker Keycloak.

## ✨ Fonctionnalités

- **Design moderne** : Interface épurée et professionnelle
- **Responsive** : Compatible mobile, tablette et desktop
- **Couleurs CHIFT** : Palette de couleurs officielle
  - Bleu principal : `#0E6B85`
  - Bleu clair : `#037ea0`
  - Bleu clair 2 : `#0491b8`
- **Logo intégré** : Logo SVG professionnel
- **Footer** : Copyright CHIFT automatique
- **Messages français** : Interface entièrement traduite
- **Accessibilité** : Conforme aux standards WCAG

## 🏗️ Structure

```
keycloak-themes/chift-theme/
├── theme.properties              # Configuration principale
├── login/                        # Pages d'authentification
│   ├── theme.properties
│   ├── template.ftl             # Template principal avec CSS intégré
│   ├── login.ftl                # Page de connexion
│   ├── login-reset-password.ftl # Réinitialisation mot de passe
│   ├── login-update-password.ftl# Mise à jour mot de passe
│   ├── error.ftl                # Page d'erreur
│   ├── login-otp.ftl            # Authentification 2FA
│   ├── login-verify-email.ftl   # Vérification email
│   └── messages/
│       └── messages_fr.properties # Messages français
├── account/                      # Pages de compte utilisateur
│   ├── theme.properties
│   ├── account.ftl
│   └── template.ftl
├── email/                        # Templates d'emails
│   ├── theme.properties
│   └── html/
│       └── email-verification.ftl
└── resources/                    # Ressources statiques
    ├── css/
    │   └── style.css            # Styles CSS (de secours)
    └── img/
        ├── logo_placeholder.svg  # Logo CHIFT
        └── favicon.ico          # Favicon
```

## 🚀 Installation et Déploiement

### 1. Déploiement automatique

```bash
# Exécuter le script de déploiement
./deploy-theme.sh

# Le script copie les fichiers dans le container Keycloak
# et redémarre le service
```

### 2. Configuration manuelle

1. **Copie des fichiers** :
```bash
docker cp keycloak-themes/ chiftbackend-keycloak-1:/opt/keycloak/themes/
```

2. **Redémarrage de Keycloak** :
```bash
docker-compose restart keycloak
```

3. **Configuration du realm** :
- Aller dans l'Admin Console Keycloak
- Sélectionner le realm `chift`
- Aller dans `Realm Settings > Themes`
- Définir tous les thèmes sur `chift-theme`

## 🎯 Test et Validation

### Script de test

```bash
# Lancer les tests de validation
./test-theme.sh
```

### Tests manuels recommandés

1. **Responsivité** :
   - Mobile : 375px x 667px
   - Tablette : 768px x 1024px
   - Desktop : 1200px x 800px

2. **Fonctionnalités** :
   - ✅ Page de connexion avec logo
   - ✅ Messages d'erreur
   - ✅ Réinitialisation mot de passe
   - ✅ Footer copyright
   - ✅ Design cohérent sur toutes les pages

3. **Navigation** :
   - Test de tous les liens
   - Validation des formulaires
   - Messages de retour utilisateur

## 🎨 Personnalisation

### Couleurs

Les couleurs sont définies dans `template.ftl` :

```css
:root {
  --chift-blue: #0E6B85;
  --chift-light-blue: #037ea0;
  --chift-light-blue-2: #0491b8;
  /* ... autres couleurs ... */
}
```

### Logo

Pour remplacer le logo :
1. Remplacer `resources/img/logo_placeholder.svg`
2. Maintenir la taille 48x48px
3. Redéployer le thème

### Messages

Messages français dans `login/messages/messages_fr.properties`.

## 🔧 Développement

### Mode développement

Le `docker-compose.yml` est configuré pour le développement :

```yaml
environment:
  KC_SPI_THEME_STATIC_MAX_AGE: -1
  KC_SPI_THEME_CACHE_THEMES: false
  KC_SPI_THEME_CACHE_TEMPLATES: false
```

### Structure CSS

Le CSS est intégré directement dans `template.ftl` pour :
- Garantir le chargement des styles
- Éviter les problèmes de cache
- Simplifier le déploiement

### Responsive Design

Media queries définies pour :
- Mobile : `@media (max-width: 640px)`
- Tablette : `@media (max-width: 1024px)`
- Desktop : tailles supérieures

## 📱 Compatible

- ✅ Keycloak 20+
- ✅ Login Theme
- ✅ Account Theme  
- ✅ Email Theme
- ✅ Docker/Kubernetes
- ✅ Tous navigateurs modernes
- ✅ Mobile et Desktop

## 🔄 Maintenance

### Mise à jour

1. Modifier les fichiers du thème
2. Exécuter `./deploy-theme.sh`
3. Tester avec `./test-theme.sh`

### Sauvegarde

Les thèmes sont persistés via volumes Docker :

```yaml
volumes:
  - ./keycloak-themes:/opt/keycloak/themes
```

## 🆘 Dépannage

### Thème non appliqué

1. Vérifier la configuration du realm
2. Vider le cache navigateur
3. Redémarrer Keycloak :
```bash
docker-compose restart keycloak
```

### Styles non chargés

1. Vérifier que les styles sont dans `template.ftl`
2. Contrôler les logs Docker :
```bash
docker-compose logs keycloak
```

### Logo non affiché

1. Vérifier le chemin : `${url.resourcesPath}/img/logo_placeholder.svg`
2. Contrôler les permissions des fichiers
3. Tester l'accès direct à l'image

## 🎉 Résultat Final

Le thème CHIFT offre :
- Une expérience utilisateur moderne et professionnelle
- Une interface entièrement responsive
- Une intégration parfaite avec l'identité visuelle CHIFT
- Des messages d'erreur élégants et informatifs
- Un footer avec copyright automatique
- Une navigation intuitive sur tous les appareils

---

**Développé pour CHIFT** • © 2025 CHIFT. Tous droits réservés.

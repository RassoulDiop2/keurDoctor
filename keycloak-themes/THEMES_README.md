# 🎨 KeurDoctor Keycloak Themes

Ce dossier contient les thèmes personnalisés pour Keycloak dans le projet KeurDoctor.

## 📁 Structure

```
keycloak-themes/
└── keurdoctor/               # Thème principal KeurDoctor
    ├── theme.properties      # Configuration générale du thème
    └── login/               # Thème de connexion
        ├── theme.properties # Configuration du thème de connexion
        └── resources/
            └── css/
                └── keurdoctor.css  # Styles personnalisés
```

## 🎯 Fonctionnalités du Thème

- **🏥 Branding KeurDoctor** : Logo, couleurs et style médical
- **📱 Design responsive** : Adapté mobile et desktop
- **♿ Accessibilité** : Conformité aux standards d'accessibilité
- **🎨 Interface moderne** : Design épuré et professionnel
- **⚡ Animations fluides** : Transitions et effets visuels

## 🚀 Utilisation

### 1. Démarrer avec le thème
```bash
# Démarrer Keycloak avec les thèmes
./start.sh
```

### 2. Configurer le thème dans Keycloak Admin
1. Accéder à http://localhost:8080/admin
2. Se connecter avec `admin`/`admin`
3. Aller dans votre realm `KeurDoctorSecure`
4. **Realm Settings** → **Themes**
5. **Login theme** : Sélectionner `keurdoctor`
6. Cliquer **Save**

### 3. Voir le thème en action
- Aller sur http://localhost:8000
- Cliquer sur "Se connecter avec Keycloak"
- Voir le nouveau thème KeurDoctor !

## 🎨 Personnalisation

### Couleurs principales
```css
:root {
    --kd-primary: #2c5282;      /* Bleu principal */
    --kd-secondary: #3182ce;    /* Bleu secondaire */
    --kd-success: #38a169;      /* Vert succès */
    --kd-warning: #d69e2e;      /* Orange avertissement */
    --kd-error: #e53e3e;        /* Rouge erreur */
}
```

### Modifier les styles
Éditer le fichier : `keurdoctor/login/resources/css/keurdoctor.css`

### Ajouter des images
Créer un dossier : `keurdoctor/login/resources/img/`

## 🔄 Développement

En mode développement, les thèmes sont automatiquement rechargés grâce à :
- `--spi-theme-cache-themes=false`
- `--spi-theme-cache-templates=false`
- `--spi-theme-static-max-age=-1`

Pas besoin de redémarrer Keycloak après modification !

## 📚 Ressources

- [Documentation Keycloak Themes](https://www.keycloak.org/docs/latest/server_development/#_themes)
- [Keycloak Theme Development](https://keycloak.discourse.group/c/themes/8)
- [CSS Variables Reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

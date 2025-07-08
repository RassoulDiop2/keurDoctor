# 🔄 Synchronisation Automatique Django-Keycloak

## 📋 Vue d'ensemble

Ce système permet de synchroniser automatiquement les rôles attribués dans Django vers Keycloak, éliminant le besoin de configuration manuelle dans l'interface Keycloak.

## ✨ Fonctionnalités

### 🔄 Synchronisation Automatique
- **Attribution de rôle** : Quand l'admin attribue un rôle via le dashboard Django, il est automatiquement synchronisé vers Keycloak
- **Déblocage d'utilisateur** : Les rôles sont resynchronisés lors du déblocage d'un utilisateur
- **Gestion des sessions** : Les sessions Keycloak sont invalidées pour forcer la reconnexion avec les nouveaux rôles

### 🛠️ Outils de Synchronisation Manuelle
- **Bouton "Sync Keycloak"** : Dans l'interface admin pour synchroniser un utilisateur spécifique
- **Commande de management** : `python manage.py sync_roles_to_keycloak` pour synchroniser tous les utilisateurs

## 🚀 Utilisation

### 1. Attribution de Rôle (Automatique)
1. Aller dans `/administration/securite/`
2. Dans la section "Utilisateurs en attente de rôle"
3. Cliquer sur "Attribuer ce rôle" ou "Attribuer un rôle"
4. Le rôle est automatiquement synchronisé vers Keycloak

### 2. Synchronisation Manuelle
1. Aller dans `/administration/securite/`
2. Cliquer sur le bouton "Sync Keycloak" à côté de l'utilisateur
3. Confirmer la synchronisation

### 3. Synchronisation en Ligne de Commande

```bash
# Synchroniser tous les utilisateurs
python manage.py sync_roles_to_keycloak

# Mode dry-run (simulation)
python manage.py sync_roles_to_keycloak --dry-run

# Synchroniser un utilisateur spécifique
python manage.py sync_roles_to_keycloak --user-email user@example.com

# Forcer la synchronisation malgré les erreurs
python manage.py sync_roles_to_keycloak --force
```

## 🔧 Configuration Requise

### Keycloak
- **Rôles créés** : `admin`, `medecin`, `patient`
- **Mapper configuré** : `realm-roles` pour inclure les rôles dans les tokens
- **API Admin** : Accessible avec les credentials configurés

### Django Settings
```python
# Configuration Keycloak Admin
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"
KEYCLOAK_SERVER_URL = "http://localhost:8080"
OIDC_REALM = "KeurDoctorSecure"
```

## 📊 Workflow Complet

### 1. Inscription Utilisateur
```
Utilisateur s'inscrit → Rôle demandé stocké → Utilisateur créé dans Keycloak (sans rôle)
```

### 2. Attribution de Rôle par l'Admin
```
Admin attribue rôle → Django mis à jour → Keycloak synchronisé → Sessions invalidées
```

### 3. Connexion Utilisateur
```
Utilisateur se connecte → Rôle vérifié → Accès accordé/refusé selon le rôle autorisé
```

## 🛡️ Sécurité

### Contrôles de Sécurité
- **Vérification des rôles** : Seuls les rôles autorisés sont synchronisés
- **Invalidation des sessions** : Les sessions sont invalidées après modification
- **Logging complet** : Toutes les opérations sont loggées
- **Gestion d'erreurs** : Erreurs gérées gracieusement avec notifications

### Alertes de Sécurité
- **Modification de rôle** : Alerte créée pour chaque attribution
- **Erreurs de synchronisation** : Alertes en cas d'échec de synchronisation
- **Tentatives de connexion** : Historique des tentatives avec rôles

## 🔍 Dépannage

### Problèmes Courants

#### 1. Erreur "Impossible d'obtenir le token admin"
```bash
# Vérifier les credentials
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"

# Vérifier que Keycloak est démarré
curl http://localhost:8080/health
```

#### 2. Erreur "Utilisateur non trouvé dans Keycloak"
```bash
# Vérifier que l'utilisateur existe dans Keycloak
# Aller dans http://localhost:8080/admin → Users
```

#### 3. Erreur "Rôle non trouvé"
```bash
# Vérifier que les rôles existent dans Keycloak
# Aller dans http://localhost:8080/admin → Realm roles
```

### Commandes de Diagnostic

```bash
# Vérifier la configuration
python manage.py sync_roles_to_keycloak --dry-run

# Synchroniser un utilisateur spécifique
python manage.py sync_roles_to_keycloak --user-email admin@keurdoctor.com

# Forcer la synchronisation
python manage.py sync_roles_to_keycloak --force
```

## 📝 Logs

### Logs Django
```python
# Logs de synchronisation
logger.info(f"Synchronisation Keycloak réussie pour {email} - Rôle: {role}")
logger.error(f"Erreur lors de la synchronisation Keycloak: {e}")
```

### Logs Keycloak
- Vérifier les logs Keycloak pour les erreurs d'API
- `/opt/keycloak/logs/` (Docker) ou logs du serveur

## 🎯 Avantages

1. **Automatisation** : Plus besoin de configuration manuelle dans Keycloak
2. **Cohérence** : Synchronisation garantie entre Django et Keycloak
3. **Sécurité** : Contrôle strict des rôles avec blocage automatique
4. **Traçabilité** : Historique complet des modifications
5. **Flexibilité** : Outils manuels et automatiques disponibles

## 🔮 Évolutions Futures

- **Synchronisation bidirectionnelle** : Keycloak → Django
- **Webhooks** : Notifications en temps réel
- **Interface de monitoring** : Dashboard de synchronisation
- **Synchronisation par lots** : Optimisation pour de gros volumes 
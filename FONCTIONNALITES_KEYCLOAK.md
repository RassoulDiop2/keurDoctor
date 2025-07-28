# 🛡️ Fonctionnalités Keycloak utilisées dans KeurDoctor

## 1. Authentification OpenID Connect (OIDC)
- **Protocole utilisé** : OpenID Connect (OIDC) via Keycloak
- **Utilité** : Authentification centralisée, SSO (Single Sign-On), gestion sécurisée des sessions
- **Configuration** :
  - Client OIDC : `django-KDclient`
  - Realm : `KeurDoctorSecure`
  - Endpoints utilisés : `/auth`, `/token`, `/userinfo`, `/logout`
- **Rôle** : Permet aux utilisateurs de se connecter via Keycloak, avec gestion des tokens JWT

## 2. Gestion des rôles et groupes
- **Rôles Realm** : `admin`, `medecin`, `patient`
- **Groupes** : `administrateurs`, `medecins`, `patients`
- **Utilité** : Contrôle d'accès granulaire, séparation des permissions par type d'utilisateur
- **Synchronisation** :
  - Les utilisateurs sont automatiquement ajoutés aux groupes correspondant à leur rôle
  - Les rôles sont attribués côté Keycloak et synchronisés avec Django

## 3. Synchronisation automatique avec Django
- **Mécanisme** : Signals Django (`post_save`) → API admin Keycloak
- **Utilité** :
  - Création/mise à jour d'utilisateur dans Keycloak dès qu'un utilisateur est créé/modifié dans Django
  - Nettoyage automatique des données (prénom, nom, email)
  - Mise à jour des groupes et rôles
- **Avantage** : Cohérence entre la base Django et Keycloak sans intervention manuelle

## 4. Gestion des mots de passe (temporaire/permanent)
- **Mot de passe permanent** :
  - Lors de la création, le mot de passe est défini comme permanent (`temporary: False`)
  - Évite l'écran "Update Account Information" à la première connexion
- **Réinitialisation** :
  - Possible via l'API admin Keycloak ou l'interface Keycloak

## 5. Actions requises (`requiredActions`)
- **Utilité** : Forcer certaines actions à la connexion (ex : changer le mot de passe, vérifier l'email)
- **Dans ce projet** :
  - Les actions requises sont supprimées automatiquement pour éviter les blocages
  - Email toujours marqué comme vérifié (`emailVerified: true`)

## 6. Gestion des utilisateurs
- **Création** :
  - Via Django (admin métier ou inscription)
  - Synchronisation immédiate dans Keycloak
- **Modification** :
  - Toute modification dans Django est répercutée dans Keycloak
- **Désactivation** :
  - Un utilisateur peut être désactivé côté Django ou Keycloak (champ `enabled`)
- **Suppression** :
  - Possible via l'API admin Keycloak ou les scripts de nettoyage

## 7. Sécurité
- **Email vérifié** : Toujours à `true` pour éviter les écrans de vérification
- **Sessions** : Gérées par Keycloak (tokens JWT, refresh, logout global)
- **Protection CSRF/XSS** : Gérée côté Django
- **Audit** : Toutes les actions sont loguées côté Django

## 8. Intégration avec l'API admin Keycloak
- **Utilisation** :
  - Création, modification, suppression d'utilisateurs
  - Attribution de rôles et groupes
  - Réinitialisation de mot de passe
  - Vérification des statuts (enabled, emailVerified, requiredActions)
- **Librairie** : Utilisation directe de l'API REST Keycloak via `requests`

## 9. Exemples de scénarios d'usage
- **Création d'un médecin** :
  - L'admin crée un utilisateur dans Django → Ajout dans Keycloak, groupe `medecins`, rôle `medecin`, email vérifié
- **Première connexion** :
  - L'utilisateur se connecte directement sans écran de changement de mot de passe
- **Changement de rôle** :
  - Modification dans Django → Synchronisation immédiate dans Keycloak
- **Blocage d'un utilisateur** :
  - Désactivation dans Django → Désactivation dans Keycloak (`enabled: false`)

## 10. Conseils de sécurité et bonnes pratiques
- **Changer le mot de passe admin par défaut** après installation
- **Limiter l'accès à l'API admin Keycloak**
- **Activer HTTPS en production**
- **Vérifier régulièrement les logs de sécurité**
- **Utiliser des mots de passe forts pour tous les comptes**
- **Sauvegarder la base Keycloak régulièrement**

## 11. Documentation officielle
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Keycloak REST API](https://www.keycloak.org/docs-api/21.1.1/rest-api/index.html)
- [OpenID Connect](https://openid.net/connect/)

---

**Résumé** :
Keycloak est utilisé dans KeurDoctor comme serveur d'authentification centralisé, garantissant la sécurité, la gestion des rôles, la synchronisation automatique avec Django, et une expérience utilisateur fluide et sécurisée. 
# 🔐 Authentification RFID + OTP - KeurDoctor

## 📋 Vue d'Ensemble

Le système d'authentification RFID + OTP de KeurDoctor permet aux **patients** de se connecter de manière sécurisée en utilisant leur carte RFID personnelle combinée à un code OTP (One-Time Password).

## 🎯 Fonctionnalités

### ✅ Authentification Double Facteur
- **Premier facteur** : Carte RFID personnelle
- **Deuxième facteur** : Code OTP à 6 chiffres
- **Sécurité renforcée** : Protection contre l'usurpation d'identité

### 👥 Utilisateurs Ciblés
- **Exclusivement réservé aux patients**
- Accès direct au dashboard patient après authentification
- Interface adaptée et sécurisée

### 🔄 Workflow d'Authentification

```
1. Patient accède à /patient/rfid/login/
2. Saisit son email et l'UID de sa carte RFID
3. Validation de la carte RFID
4. Redirection vers /patient/rfid/otp/
5. Saisie du code OTP (123456 pour les tests)
6. Accès direct au dashboard patient (/patient/)
```

## 🛠️ Implémentation Technique

### 📁 Fichiers Principaux

#### Vues (`comptes/views.py`)
- `patient_rfid_login()` : Page de connexion RFID
- `patient_rfid_otp()` : Validation OTP
- `api_rfid_patient_auth()` : API pour validation RFID + OTP

#### Templates
- `templates/rfid/patient_rfid_login.html` : Interface de connexion RFID
- `templates/rfid/patient_rfid_otp.html` : Interface de validation OTP
- `templates/authentification/methodes.html` : Comparaison des méthodes

#### URLs (`comptes/urls.py`)
```python
path('patient/rfid/login/', views.patient_rfid_login, name='patient_rfid_login'),
path('patient/rfid/otp/', views.patient_rfid_otp, name='patient_rfid_otp'),
path('api/rfid-patient-auth/', views.api_rfid_patient_auth, name='api_rfid_patient_auth'),
```

### 🔒 Sécurité

#### Vérifications Effectuées
1. **Rôle utilisateur** : Seuls les patients peuvent utiliser cette méthode
2. **Statut du compte** : Vérification que l'utilisateur n'est pas bloqué
3. **Carte RFID** : Validation de l'existence et de l'activation de la carte
4. **Code OTP** : Validation du code à 6 chiffres
5. **Session** : Gestion sécurisée des sessions temporaires

#### Historique et Audit
- Enregistrement de toutes les tentatives d'authentification
- Traçabilité complète des accès
- Alertes de sécurité en cas d'anomalie

## 🚀 Utilisation

### 📋 Prérequis
1. **Compte patient** créé dans le système
2. **Carte RFID** enregistrée et associée au compte
3. **Code OTP** disponible (SMS ou application)

### 🔧 Configuration

#### 1. Créer des utilisateurs de test
```bash
python manage.py create_rfid_test_users
```

#### 2. Enregistrer une carte RFID
- Accéder à `/rfid/enregistrer/`
- Saisir l'UID de la carte RFID
- Associer à un compte patient

#### 3. Tester l'authentification
- Aller sur `/patient/rfid/login/`
- Utiliser les données de test :
  - Email : `patient.rfid.test1@keurdoctor.com`
  - RFID : `RFID001234567890`
  - OTP : `123456`

### 🎯 URLs de Test

| URL | Description |
|-----|-------------|
| `/patient/rfid/login/` | Page de connexion RFID |
| `/patient/rfid/otp/` | Validation OTP |
| `/authentification/methodes/` | Comparaison des méthodes |
| `/rfid/enregistrer/` | Enregistrement carte RFID |

## 📊 Données de Test

### 👥 Utilisateurs de Test Créés

| Email | Nom | RFID | OTP |
|-------|-----|------|-----|
| `patient.rfid.test1@keurdoctor.com` | Marie Dupont | `RFID001234567890` | `123456` |
| `patient.rfid.test2@keurdoctor.com` | Jean Martin | `RFID009876543210` | `123456` |
| `patient.rfid.test3@keurdoctor.com` | Sophie Bernard | `RFID005566778899` | `123456` |

### 🔧 Commandes de Gestion

```bash
# Créer les utilisateurs de test
python manage.py create_rfid_test_users

# Supprimer les utilisateurs de test
python manage.py create_rfid_test_users --clear
```

## 🔄 Comparaison avec l'Authentification Standard

| Caractéristique | Standard | RFID + OTP |
|-----------------|----------|-------------|
| **Utilisateurs** | Tous | Patients uniquement |
| **Facteurs** | 2 (Email + MDP) | 2 (RFID + OTP) |
| **Sécurité** | Élevée | Très élevée |
| **Configuration** | Aucune | Carte RFID requise |
| **Accès** | Redirection selon rôle | Direct patient |

## 🛡️ Sécurité Avancée

### 🔐 Chiffrement
- Données sensibles chiffrées avec Fernet
- Clés de chiffrement sécurisées
- Protection des informations personnelles

### 📝 Audit Trail
- Historique complet des authentifications
- Logs détaillés des tentatives
- Alertes automatiques en cas d'anomalie

### 🚫 Protection contre les Attaques
- Limitation des tentatives de connexion
- Blocage automatique après échecs
- Validation stricte des rôles

## 🔮 Évolutions Futures

### 📱 Intégration Mobile
- Application mobile pour génération OTP
- Notifications push pour les codes
- Interface tactile optimisée

### 🔗 Intégration Hardware
- Lecteurs RFID physiques
- Synchronisation temps réel
- Validation biométrique

### 🌐 API REST
- Endpoints pour applications tierces
- Authentification par API
- Webhooks pour notifications

## 📞 Support

Pour toute question ou problème :
- Consulter la documentation technique
- Vérifier les logs d'erreur
- Tester avec les utilisateurs de test fournis

---

**KeurDoctor** - Système d'authentification RFID + OTP sécurisé pour les patients 
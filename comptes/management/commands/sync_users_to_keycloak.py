from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import requests
import json


class Command(BaseCommand):
    help = 'Synchronise les utilisateurs Django vers Keycloak'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keycloak-url',
            default='http://localhost:8080',
            help='URL de Keycloak (défaut: http://localhost:8080)',
        )
        parser.add_argument(
            '--realm',
            default='KeurDoctorSecure',
            help='Nom du realm Keycloak (défaut: KeurDoctorSecure)',
        )
        parser.add_argument(
            '--admin-user',
            default='admin',
            help='Utilisateur admin Keycloak (défaut: admin)',
        )
        parser.add_argument(
            '--admin-password',
            default='admin',
            help='Mot de passe admin Keycloak (défaut: admin)',
        )

    def handle(self, *args, **options):
        keycloak_url = options['keycloak_url']
        realm = options['realm']
        admin_user = options['admin_user']
        admin_password = options['admin_password']

        self.stdout.write("🔄 Début de la synchronisation Django → Keycloak...")

        try:
            # 1. Obtenir le token admin
            token = self.get_admin_token(keycloak_url, admin_user, admin_password)
            if not token:
                return

            # 2. Synchroniser chaque utilisateur Django
            django_users = User.objects.all()
            success_count = 0
            error_count = 0

            for user in django_users:
                try:
                    # Mapper les groupes Django aux rôles Keycloak
                    user_groups = [g.name for g in user.groups.all()]
                    keycloak_roles = []
                    
                    if 'admin' in user_groups:
                        keycloak_roles.append('admin')
                    elif 'medecin' in user_groups:
                        keycloak_roles.append('medecin')
                    elif 'patient' in user_groups:
                        keycloak_roles.append('patient')
                    else:
                        keycloak_roles.append('patient')  # Défaut

                    # Créer l'utilisateur dans Keycloak
                    if self.create_keycloak_user(keycloak_url, realm, token, user, keycloak_roles):
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {user.username} synchronisé vers Keycloak")
                        )
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"❌ Erreur pour {user.username}: {str(e)}")
                    )

            # Résumé
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS(f"🎉 Synchronisation terminée!"))
            self.stdout.write(f"✅ Succès: {success_count}")
            self.stdout.write(f"❌ Erreurs: {error_count}")
            self.stdout.write(f"\n🔍 Vérifiez dans Keycloak Admin: {keycloak_url}/admin")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur de synchronisation: {str(e)}")
            )

    def get_admin_token(self, keycloak_url, admin_user, admin_password):
        """Obtenir le token d'authentification admin"""
        try:
            url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': admin_user,
                'password': admin_password
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                self.stdout.write("✅ Token admin obtenu")
                return token_data['access_token']
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur d'authentification Keycloak: {response.status_code}")
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Keycloak inaccessible: {str(e)}")
            )
            self.stdout.write("💡 Vérifiez que Keycloak est démarré avec: ./start.sh")
            return None

    def create_keycloak_user(self, keycloak_url, realm, token, django_user, roles):
        """Créer un utilisateur dans Keycloak"""
        try:
            # 1. Créer l'utilisateur
            url = f"{keycloak_url}/admin/realms/{realm}/users"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            user_data = {
                'username': django_user.username,
                'email': django_user.email,
                'firstName': django_user.first_name,
                'lastName': django_user.last_name,
                'enabled': True,
                'emailVerified': True,
                'credentials': [{
                    'type': 'password',
                    'value': self.get_user_password(django_user.username),
                    'temporary': False  # Mot de passe permanent pour les tests
                }]
            }

            response = requests.post(url, headers=headers, json=user_data, timeout=10)
            
            if response.status_code == 201:
                # 2. Obtenir l'ID de l'utilisateur créé
                user_id = self.get_user_id(keycloak_url, realm, token, django_user.username)
                
                if user_id:
                    # 3. Assigner les rôles
                    self.assign_roles(keycloak_url, realm, token, user_id, roles)
                    return True
                    
            elif response.status_code == 409:
                self.stdout.write(f"⚠️ {django_user.username} existe déjà dans Keycloak")
                return True
                
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Erreur création {django_user.username}: {response.status_code}")
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur pour {django_user.username}: {str(e)}")
            )
            return False

    def get_user_id(self, keycloak_url, realm, token, username):
        """Obtenir l'ID d'un utilisateur Keycloak"""
        try:
            url = f"{keycloak_url}/admin/realms/{realm}/users?username={username}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    return users[0]['id']
            return None
            
        except Exception:
            return None

    def assign_roles(self, keycloak_url, realm, token, user_id, roles):
        """Assigner des rôles à un utilisateur"""
        try:
            for role_name in roles:
                # Obtenir l'ID du rôle
                role_url = f"{keycloak_url}/admin/realms/{realm}/roles/{role_name}"
                headers = {'Authorization': f'Bearer {token}'}
                
                role_response = requests.get(role_url, headers=headers, timeout=10)
                
                if role_response.status_code == 200:
                    role_data = role_response.json()
                    
                    # Assigner le rôle
                    assign_url = f"{keycloak_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
                    assign_data = [role_data]
                    
                    requests.post(assign_url, headers=headers, json=assign_data, timeout=10)
                    
        except Exception as e:
            self.stdout.write(f"⚠️ Erreur assignation rôle: {str(e)}")

    def get_user_password(self, username):
        """Obtenir le mot de passe pour un utilisateur donné"""
        # Mots de passe spécifiques pour les utilisateurs de test
        passwords = {
            'admin': 'admin123',
            'dr.laye': 'medecin123',
            'dr.fatou': 'medecin123',
            'patient.baye': 'patient123',
            'patient.aida': 'patient123',
            'test': 'test123'
        }
        
        return passwords.get(username, 'DefaultPassword123!')

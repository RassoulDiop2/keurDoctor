from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import requests
import json


class Command(BaseCommand):
    help = 'Corrige les mots de passe des utilisateurs de test dans Keycloak'

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

    def handle(self, *args, **options):
        keycloak_url = options['keycloak_url']
        realm = options['realm']

        self.stdout.write("🔧 Correction des mots de passe Keycloak...")

        try:
            # 1. Obtenir le token admin
            token = self.get_admin_token(keycloak_url)
            if not token:
                return

            # 2. Définir les utilisateurs de test avec leurs vrais mots de passe
            test_users = {
                'admin': 'Admin123!',
                'abdoulaye': 'laye123!',
                'test': 'Test123!'
            }

            success_count = 0
            error_count = 0

            # 3. Mettre à jour chaque utilisateur
            for username, password in test_users.items():
                if self.update_user_password(keycloak_url, realm, token, username, password):
                    self.stdout.write(f"✅ Mot de passe de '{username}' mis à jour")
                    success_count += 1
                else:
                    self.stdout.write(f"❌ Erreur pour '{username}'")
                    error_count += 1

            # 4. Résumé
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("🎉 Correction terminée!"))
            self.stdout.write(f"✅ Succès: {success_count}")
            self.stdout.write(f"❌ Erreurs: {error_count}")
            
            if success_count > 0:
                self.stdout.write("\n📋 Vous pouvez maintenant vous connecter avec :")
                for username, password in test_users.items():
                    self.stdout.write(f"  👤 {username} / {password}")
                
                self.stdout.write(f"\n🌐 Testez la connexion: http://localhost:8000")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur générale: {str(e)}")
            )

    def get_admin_token(self, keycloak_url):
        """Obtenir le token d'accès admin Keycloak"""
        try:
            url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': 'admin',
                'password': 'admin'
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

    def update_user_password(self, keycloak_url, realm, token, username, password):
        """Mettre à jour le mot de passe d'un utilisateur dans Keycloak"""
        try:
            # 1. Chercher l'utilisateur par username
            search_url = f"{keycloak_url}/admin/realms/{realm}/users?username={username}&exact=true"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return False
            
            users = response.json()
            if not users:
                self.stdout.write(f"⚠️ Utilisateur '{username}' non trouvé dans Keycloak")
                return False
            
            user_id = users[0]['id']
            
            # 2. Mettre à jour le mot de passe
            password_url = f"{keycloak_url}/admin/realms/{realm}/users/{user_id}/reset-password"
            
            password_data = {
                'type': 'password',
                'value': password,
                'temporary': False  # Mot de passe permanent
            }
            
            response = requests.put(password_url, headers=headers, json=password_data, timeout=10)
            
            return response.status_code == 204  # 204 = No Content = succès
            
        except Exception as e:
            self.stdout.write(f"⚠️ Erreur pour {username}: {str(e)}")
            return False

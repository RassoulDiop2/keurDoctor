from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import requests
import json


class Command(BaseCommand):
    help = 'Nettoie les sessions Keycloak expirées ou pour des utilisateurs spécifiques'

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
            '--username',
            help='Nettoyer uniquement les sessions de cet utilisateur',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Nettoyer toutes les sessions du realm',
        )

    def handle(self, *args, **options):
        keycloak_url = options['keycloak_url']
        realm = options['realm']
        username = options.get('username')
        clean_all = options.get('all')

        self.stdout.write("🧹 Nettoyage des sessions Keycloak...")

        try:
            # 1. Obtenir le token admin
            token = self.get_admin_token(keycloak_url)
            if not token:
                return

            success_count = 0
            error_count = 0

            if username:
                # Nettoyer les sessions d'un utilisateur spécifique
                if self.clean_user_sessions(keycloak_url, realm, token, username):
                    self.stdout.write(f"✅ Sessions de '{username}' nettoyées")
                    success_count = 1
                else:
                    self.stdout.write(f"❌ Erreur pour '{username}'")
                    error_count = 1
                    
            elif clean_all:
                # Nettoyer toutes les sessions du realm
                count = self.clean_all_realm_sessions(keycloak_url, realm, token)
                success_count = count
                self.stdout.write(f"✅ {count} session(s) supprimée(s)")
                
            else:
                # Nettoyer les sessions des utilisateurs Django existants
                django_users = User.objects.all()
                
                for user in django_users:
                    if self.clean_user_sessions(keycloak_url, realm, token, user.username):
                        self.stdout.write(f"✅ Sessions de '{user.username}' nettoyées")
                        success_count += 1
                    else:
                        self.stdout.write(f"⚠️ Aucune session trouvée pour '{user.username}'")

            # Résumé
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("🎉 Nettoyage terminé!"))
            self.stdout.write(f"✅ Succès: {success_count}")
            if error_count > 0:
                self.stdout.write(f"❌ Erreurs: {error_count}")

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

    def clean_user_sessions(self, keycloak_url, realm, token, username):
        """Nettoyer toutes les sessions d'un utilisateur spécifique"""
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
            
            # 2. Obtenir les sessions de l'utilisateur
            sessions_url = f"{keycloak_url}/admin/realms/{realm}/users/{user_id}/sessions"
            response = requests.get(sessions_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                sessions = response.json()
                
                # 3. Supprimer chaque session
                for session in sessions:
                    session_id = session['id']
                    delete_url = f"{keycloak_url}/admin/realms/{realm}/sessions/{session_id}"
                    delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                    
                    if delete_response.status_code != 204:
                        self.stdout.write(f"⚠️ Erreur suppression session {session_id}")
                
                return len(sessions) > 0
            else:
                return False
                
        except Exception as e:
            self.stdout.write(f"⚠️ Erreur pour {username}: {str(e)}")
            return False

    def clean_all_realm_sessions(self, keycloak_url, realm, token):
        """Supprimer toutes les sessions actives du realm"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Obtenir toutes les sessions du realm
            sessions_url = f"{keycloak_url}/admin/realms/{realm}/sessions"
            response = requests.get(sessions_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                sessions = response.json()
                count = 0
                
                for session in sessions:
                    session_id = session['id']
                    delete_url = f"{keycloak_url}/admin/realms/{realm}/sessions/{session_id}"
                    delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                    
                    if delete_response.status_code == 204:
                        count += 1
                
                return count
            else:
                return 0
                
        except Exception as e:
            self.stdout.write(f"⚠️ Erreur lors du nettoyage global: {str(e)}")
            return 0

import os

kc_base_url = os.getenv('KEYCLOAK_BASE_URL')
kc_realm = os.getenv('KEYCLOAK_REALM')
kc_username = os.getenv('KEYCLOAK_USERNAME')
kc_password = os.getenv('KEYCLOAK_PASSWORD')

if not (kc_base_url and kc_realm and kc_username and kc_password):
	raise Exception("Missing Keycloak configuration")

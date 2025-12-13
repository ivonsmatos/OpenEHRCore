"""
SMART on FHIR Service

Sprint 32: SMART App Launch Protocol

Features:
- OAuth2 scopes for FHIR resources
- Launch context (patient, encounter)
- Token introspection
- Capability statement
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid
import base64
import hashlib

logger = logging.getLogger(__name__)


class SMARTService:
    """
    SMART on FHIR implementation for app authorization.
    
    Implements:
    - SMART App Launch Framework
    - OAuth2 authorization with FHIR scopes
    - Launch context injection
    """
    
    # Standard SMART scopes
    SCOPES = {
        # Patient-level scopes
        'patient/*.read': 'Read all patient data',
        'patient/*.write': 'Write all patient data',
        'patient/Patient.read': 'Read patient demographics',
        'patient/Observation.read': 'Read observations',
        'patient/Condition.read': 'Read conditions',
        'patient/MedicationRequest.read': 'Read medications',
        'patient/AllergyIntolerance.read': 'Read allergies',
        'patient/Immunization.read': 'Read immunizations',
        'patient/DiagnosticReport.read': 'Read diagnostic reports',
        'patient/Encounter.read': 'Read encounters',
        
        # User-level scopes
        'user/*.read': 'Read all data user has access to',
        'user/*.write': 'Write all data user has access to',
        'user/Patient.read': 'Read any patient demographics',
        'user/Patient.write': 'Write any patient demographics',
        'user/Practitioner.read': 'Read practitioner data',
        
        # System scopes
        'system/*.read': 'System-level read access',
        'system/Patient.read': 'System read patient data',
        
        # Launch scopes
        'launch': 'Get launch context',
        'launch/patient': 'Get patient context on launch',
        'launch/encounter': 'Get encounter context on launch',
        
        # OpenID scopes
        'openid': 'OpenID Connect authentication',
        'profile': 'User profile information',
        'fhirUser': 'FHIR user resource',
        'offline_access': 'Refresh token access',
    }
    
    def __init__(self):
        self.authorization_codes = {}  # In-memory storage (use Redis in production)
        self.access_tokens = {}
        self.refresh_tokens = {}
    
    def get_capability_statement(self, base_url: str) -> Dict:
        """
        Generate SMART-enabled CapabilityStatement.
        """
        return {
            'resourceType': 'CapabilityStatement',
            'status': 'active',
            'date': datetime.utcnow().isoformat(),
            'kind': 'instance',
            'software': {
                'name': 'OpenEHRCore',
                'version': '1.0.0'
            },
            'implementation': {
                'description': 'OpenEHRCore FHIR Server',
                'url': base_url
            },
            'fhirVersion': '4.0.1',
            'format': ['json'],
            'rest': [{
                'mode': 'server',
                'security': {
                    'cors': True,
                    'service': [{
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/restful-security-service',
                            'code': 'SMART-on-FHIR',
                            'display': 'SMART on FHIR'
                        }]
                    }],
                    'extension': [{
                        'url': 'http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris',
                        'extension': [
                            {'url': 'authorize', 'valueUri': f'{base_url}/auth/authorize'},
                            {'url': 'token', 'valueUri': f'{base_url}/auth/token'},
                            {'url': 'introspect', 'valueUri': f'{base_url}/auth/introspect'},
                            {'url': 'revoke', 'valueUri': f'{base_url}/auth/revoke'}
                        ]
                    }]
                }
            }]
        }
    
    def get_well_known_config(self, base_url: str) -> Dict:
        """
        Get SMART configuration for .well-known/smart-configuration.
        """
        return {
            'issuer': base_url,
            'authorization_endpoint': f'{base_url}/auth/authorize',
            'token_endpoint': f'{base_url}/auth/token',
            'introspection_endpoint': f'{base_url}/auth/introspect',
            'revocation_endpoint': f'{base_url}/auth/revoke',
            'jwks_uri': f'{base_url}/.well-known/jwks.json',
            'response_types_supported': ['code'],
            'grant_types_supported': ['authorization_code', 'refresh_token'],
            'scopes_supported': list(self.SCOPES.keys()),
            'code_challenge_methods_supported': ['S256'],
            'token_endpoint_auth_methods_supported': ['client_secret_basic', 'client_secret_post'],
            'capabilities': [
                'launch-ehr',
                'launch-standalone',
                'client-public',
                'client-confidential-symmetric',
                'context-ehr-patient',
                'context-ehr-encounter',
                'context-standalone-patient',
                'permission-offline',
                'permission-patient',
                'permission-user',
                'sso-openid-connect'
            ]
        }
    
    def validate_scopes(self, requested_scopes: List[str]) -> Dict[str, Any]:
        """
        Validate requested scopes.
        
        Returns:
            Dict with valid scopes and any errors
        """
        valid_scopes = []
        invalid_scopes = []
        
        for scope in requested_scopes:
            if scope in self.SCOPES or scope.startswith('patient/') or scope.startswith('user/'):
                valid_scopes.append(scope)
            else:
                invalid_scopes.append(scope)
        
        return {
            'valid': len(invalid_scopes) == 0,
            'scopes': valid_scopes,
            'invalid_scopes': invalid_scopes
        }
    
    def create_authorization(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = 'S256',
        launch_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create authorization code for SMART app.
        """
        code = str(uuid.uuid4())
        
        self.authorization_codes[code] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scopes': scopes,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'launch_context': launch_context or {},
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        logger.info(f"Created authorization code for client {client_id}")
        
        return {
            'code': code,
            'state': state,
            'redirect_uri': redirect_uri
        }
    
    def exchange_code(
        self,
        code: str,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        """
        auth_data = self.authorization_codes.get(code)
        
        if not auth_data:
            return {'error': 'invalid_grant', 'error_description': 'Authorization code not found'}
        
        # Verify client
        if auth_data['client_id'] != client_id:
            return {'error': 'invalid_client', 'error_description': 'Client ID mismatch'}
        
        if auth_data['redirect_uri'] != redirect_uri:
            return {'error': 'invalid_grant', 'error_description': 'Redirect URI mismatch'}
        
        # Verify PKCE if used
        if auth_data.get('code_challenge'):
            if not code_verifier:
                return {'error': 'invalid_grant', 'error_description': 'Code verifier required'}
            
            if auth_data['code_challenge_method'] == 'S256':
                computed = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                ).decode().rstrip('=')
                
                if computed != auth_data['code_challenge']:
                    return {'error': 'invalid_grant', 'error_description': 'Code verifier mismatch'}
        
        # Generate tokens
        access_token = str(uuid.uuid4())
        refresh_token = str(uuid.uuid4())
        expires_in = 3600  # 1 hour
        
        token_data = {
            'client_id': client_id,
            'scopes': auth_data['scopes'],
            'launch_context': auth_data['launch_context'],
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        }
        
        self.access_tokens[access_token] = token_data
        self.refresh_tokens[refresh_token] = {
            **token_data,
            'access_token': access_token
        }
        
        # Remove used authorization code
        del self.authorization_codes[code]
        
        response = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
            'scope': ' '.join(auth_data['scopes']),
            'refresh_token': refresh_token
        }
        
        # Add launch context to response
        if auth_data['launch_context']:
            if 'patient' in auth_data['launch_context']:
                response['patient'] = auth_data['launch_context']['patient']
            if 'encounter' in auth_data['launch_context']:
                response['encounter'] = auth_data['launch_context']['encounter']
        
        logger.info(f"Exchanged code for tokens for client {client_id}")
        
        return response
    
    def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Introspect access token.
        """
        token_data = self.access_tokens.get(token)
        
        if not token_data:
            return {'active': False}
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            return {'active': False}
        
        return {
            'active': True,
            'client_id': token_data['client_id'],
            'scope': ' '.join(token_data['scopes']),
            'exp': int(expires_at.timestamp()),
            'iat': int(datetime.fromisoformat(token_data['created_at']).timestamp()),
            **token_data.get('launch_context', {})
        }
    
    def revoke_token(self, token: str) -> Dict[str, Any]:
        """
        Revoke access or refresh token.
        """
        if token in self.access_tokens:
            del self.access_tokens[token]
            return {'revoked': True}
        
        if token in self.refresh_tokens:
            # Also revoke associated access token
            access_token = self.refresh_tokens[token].get('access_token')
            if access_token and access_token in self.access_tokens:
                del self.access_tokens[access_token]
            del self.refresh_tokens[token]
            return {'revoked': True}
        
        return {'revoked': False, 'error': 'Token not found'}
    
    def filter_resources_by_scopes(
        self,
        scopes: List[str],
        resource_type: str,
        operation: str = 'read'
    ) -> bool:
        """
        Check if scopes allow access to a resource type.
        """
        # Check for wildcard scopes
        if f'patient/*.{operation}' in scopes or f'user/*.{operation}' in scopes:
            return True
        
        # Check for specific resource scope
        if f'patient/{resource_type}.{operation}' in scopes:
            return True
        
        if f'user/{resource_type}.{operation}' in scopes:
            return True
        
        return False


# Singleton instance
_smart_service = None


def get_smart_service() -> SMARTService:
    """Get SMART service singleton."""
    global _smart_service
    if _smart_service is None:
        _smart_service = SMARTService()
    return _smart_service

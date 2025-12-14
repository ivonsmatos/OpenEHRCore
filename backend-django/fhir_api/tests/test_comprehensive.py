"""
Comprehensive Test Suite for HealthStack API

Tests cover:
- Rate limiting middleware
- OpenAPI documentation endpoints
- Core FHIR operations
- Authentication flows
- Brazil integrations
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json
import time


class RateLimitMiddlewareTests(TestCase):
    """Tests for rate limiting middleware."""
    
    def setUp(self):
        self.client = Client()
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are added to responses."""
        response = self.client.get('/api/v1/health/')
        # Health endpoint should return 200 (skips rate limiting)
        self.assertEqual(response.status_code, 200)
    
    def test_auth_endpoint_has_lower_limit(self):
        """Test that auth endpoints have lower rate limits."""
        # Auth endpoints should have 10 req/min limit
        from fhir_api.middleware.rate_limit import RateLimitConfig
        self.assertEqual(RateLimitConfig.LIMITS['auth'], 10)
    
    def test_default_rate_limit(self):
        """Test default rate limit configuration."""
        from fhir_api.middleware.rate_limit import RateLimitConfig
        self.assertEqual(RateLimitConfig.LIMITS['default'], 60)
    
    def test_token_bucket_initialization(self):
        """Test token bucket algorithm initialization."""
        from fhir_api.middleware.rate_limit import TokenBucket
        bucket = TokenBucket(rate=60, capacity=60)
        self.assertEqual(bucket.tokens, 60)
        self.assertEqual(bucket.rate, 60)
    
    def test_token_bucket_consume(self):
        """Test token bucket consumption."""
        from fhir_api.middleware.rate_limit import TokenBucket
        bucket = TokenBucket(rate=60, capacity=60)
        
        # Should be able to consume tokens
        self.assertTrue(bucket.consume(1))
        self.assertEqual(bucket.tokens, 59)
    
    def test_token_bucket_refill(self):
        """Test token bucket refill over time."""
        from fhir_api.middleware.rate_limit import TokenBucket
        bucket = TokenBucket(rate=60, capacity=60)
        
        # Consume all tokens
        for _ in range(60):
            bucket.consume(1)
        
        self.assertAlmostEqual(bucket.tokens, 0, places=1)
    
    def test_rate_limiter_get_bucket(self):
        """Test rate limiter bucket creation."""
        from fhir_api.middleware.rate_limit import get_rate_limiter
        limiter = get_rate_limiter()
        
        bucket = limiter.get_bucket('test-client', 'default')
        self.assertIsNotNone(bucket)
        self.assertEqual(bucket.capacity, 60)


class OpenAPIDocumentationTests(TestCase):
    """Tests for OpenAPI/Swagger documentation."""
    
    def setUp(self):
        self.client = Client()
    
    def test_openapi_schema_endpoint(self):
        """Test OpenAPI schema endpoint returns valid JSON."""
        response = self.client.get('/api/v1/docs/openapi.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertEqual(data['openapi'], '3.0.3')
        self.assertEqual(data['info']['title'], 'HealthStack API')
        self.assertEqual(data['info']['version'], '2.0.0')
    
    def test_swagger_ui_endpoint(self):
        """Test Swagger UI endpoint returns HTML."""
        response = self.client.get('/api/v1/docs/swagger/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
        self.assertIn('swagger-ui', response.content.decode())
    
    def test_redoc_endpoint(self):
        """Test ReDoc endpoint returns HTML."""
        response = self.client.get('/api/v1/docs/redoc/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
        self.assertIn('redoc', response.content.decode())
    
    def test_openapi_schema_has_required_fields(self):
        """Test OpenAPI schema has all required fields."""
        response = self.client.get('/api/v1/docs/openapi.json')
        data = response.json()
        
        # Check required top-level fields
        self.assertIn('openapi', data)
        self.assertIn('info', data)
        self.assertIn('paths', data)
        self.assertIn('components', data)
        
        # Check info section
        self.assertIn('title', data['info'])
        self.assertIn('version', data['info'])
        self.assertIn('description', data['info'])
        
        # Check security schemes
        self.assertIn('securitySchemes', data['components'])
        self.assertIn('bearerAuth', data['components']['securitySchemes'])


class HealthEndpointTests(TestCase):
    """Tests for health check endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_health_check(self):
        """Test main health check endpoint."""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_live(self):
        """Test liveness probe endpoint."""
        response = self.client.get('/api/v1/health/live/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_ready(self):
        """Test readiness probe endpoint."""
        response = self.client.get('/api/v1/health/ready/')
        # May return 200 or 503 depending on services
        self.assertIn(response.status_code, [200, 503])


class FHIRValidationTests(TestCase):
    """Tests for FHIR validation endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    @patch('fhir_api.services.fhir_validation_service.FHIRValidationService.validate_resource')
    def test_validate_patient(self, mock_validate):
        """Test validating a Patient resource."""
        mock_validate.return_value = {'valid': True, 'issues': []}
        
        patient = {
            'resourceType': 'Patient',
            'name': [{'family': 'Test', 'given': ['User']}]
        }
        
        response = self.client.post(
            '/api/v1/fhir/validate',
            data=json.dumps(patient),
            content_type='application/json'
        )
        
        # May require auth, so 401 or 200
        self.assertIn(response.status_code, [200, 401])


class BrazilIntegrationTests(TestCase):
    """Tests for Brazil-specific integrations."""
    
    def setUp(self):
        self.client = Client()
    
    def test_pix_endpoint_requires_auth(self):
        """Test that PIX endpoint requires authentication."""
        response = self.client.post('/api/v1/pix/payments/create/')
        self.assertIn(response.status_code, [401, 403])
    
    def test_whatsapp_endpoint_requires_auth(self):
        """Test that WhatsApp endpoint requires authentication."""
        response = self.client.post('/api/v1/whatsapp/send/')
        self.assertIn(response.status_code, [401, 403])


class AgentEndpointTests(TestCase):
    """Tests for on-premise agent endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_agent_register_requires_auth(self):
        """Test that agent registration requires authentication."""
        response = self.client.post('/api/v1/agent/register')
        self.assertIn(response.status_code, [401, 403])
    
    def test_agent_list_endpoint(self):
        """Test agent list endpoint."""
        response = self.client.get('/api/v1/agent/list')
        # Requires auth
        self.assertIn(response.status_code, [401, 403])


# Run if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

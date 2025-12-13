"""
Bias Prevention Service

Implements guardrails to prevent algorithmic bias in:
- AI-generated content
- Clinical recommendations
- Drug suggestions
- Analytics exports

Compliance: LGPD, Anti-discrimination laws
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class BiasPreventionService:
    """
    Service for detecting and preventing bias in healthcare AI systems.
    
    Implements:
    - Content filtering for discriminatory terms
    - Prompt guardrails for AI
    - Audit trail for bias detection
    - Data anonymization for exports
    """
    
    # Terms that should never appear in clinical recommendations
    PROHIBITED_TERMS = {
        # Ethnic/racial bias
        'raça', 'etnia', 'negro', 'branco', 'pardo', 'indígena', 'amarelo',
        'africano', 'europeu', 'asiático', 'caucasiano', 'mulato',
        # Discriminatory language
        'inferior', 'superior', 'primitivo', 'atrasado', 'civilizado',
        # Socioeconomic bias
        'pobre', 'rico', 'favelado', 'classe baixa', 'classe alta',
        # Religious bias
        'religião', 'cristão', 'muçulmano', 'judeu', 'ateu',
        # Gender bias (unless clinically relevant)
        'histérica', 'fraca', 'sensível demais',
        # Age bias
        'velho demais', 'muito jovem para',
    }
    
    # Clinical contexts where demographic data IS appropriate
    ALLOWED_CLINICAL_CONTEXTS = {
        # Sex-specific conditions
        'gravidez', 'gestação', 'próstata', 'ovário', 'útero',
        'mama', 'testículo', 'menstruação', 'menopausa',
        # Age-specific dosing
        'pediatria', 'neonatal', 'geriátrico', 'dose por idade',
        # Clinical history requiring demographic context
        'anemia falciforme', 'talassemia', 'doença de tay-sachs',
    }
    
    # AI guardrail instructions (added to every prompt)
    AI_GUARDRAILS = """
IMPORTANT ETHICAL GUIDELINES - YOU MUST FOLLOW:
1. You must NEVER make treatment recommendations based on race or ethnicity
2. You must NEVER use discriminatory or biased language
3. You must treat all patients equally regardless of socioeconomic status
4. Base recommendations ONLY on clinical evidence and patient-specific data
5. If demographic data is mentioned, use it ONLY when clinically necessary
6. Do not assume health outcomes based on non-clinical factors
7. Report only objective clinical findings
8. Use inclusive and respectful language at all times
"""
    
    # Sensitive data patterns (for anonymization)
    PII_PATTERNS = {
        'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
        'phone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
        'email': r'[\w\.-]+@[\w\.-]+\.\w+',
        'cep': r'\d{5}-?\d{3}',
        'name_prefix': r'(Sr\.|Sra\.|Dr\.|Dra\.|Prof\.)\s*[A-ZÀ-Ú][a-zà-ú]+',
    }
    
    # Audit log
    _bias_audit_log: List[Dict] = []
    
    @classmethod
    def add_guardrails_to_prompt(cls, prompt: str) -> str:
        """
        Add bias prevention guardrails to an AI prompt.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Prompt with guardrails prepended
        """
        return f"{cls.AI_GUARDRAILS}\n\n{prompt}"
    
    @classmethod
    def check_content_for_bias(
        cls,
        content: str,
        context: str = "general"
    ) -> Tuple[bool, List[str]]:
        """
        Check content for potentially biased terms.
        
        Args:
            content: Text to check
            context: Context (general, clinical, research)
            
        Returns:
            Tuple of (has_bias, list of detected terms)
        """
        content_lower = content.lower()
        detected_terms = []
        
        # Check for prohibited terms
        for term in cls.PROHIBITED_TERMS:
            if term in content_lower:
                # Check if in allowed clinical context
                is_clinical = any(
                    ctx in content_lower 
                    for ctx in cls.ALLOWED_CLINICAL_CONTEXTS
                )
                
                if not is_clinical:
                    detected_terms.append(term)
        
        has_bias = len(detected_terms) > 0
        
        if has_bias:
            cls._log_bias_detection(content, detected_terms, context)
        
        return has_bias, detected_terms
    
    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """
        Remove or replace potentially biased terms.
        
        Args:
            content: Text to sanitize
            
        Returns:
            Sanitized text
        """
        sanitized = content
        
        for term in cls.PROHIBITED_TERMS:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            sanitized = pattern.sub('[TERMO REMOVIDO]', sanitized)
        
        return sanitized
    
    @classmethod
    def anonymize_text(cls, text: str) -> str:
        """
        Remove PII from text.
        
        Args:
            text: Text containing potential PII
            
        Returns:
            Anonymized text
        """
        anonymized = text
        
        for pii_type, pattern in cls.PII_PATTERNS.items():
            anonymized = re.sub(pattern, f'[{pii_type.upper()}_ANONIMIZADO]', anonymized)
        
        return anonymized
    
    @classmethod
    def anonymize_for_analytics(
        cls,
        data: Dict[str, Any],
        preserve_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Anonymize data for analytics/export.
        
        Args:
            data: Data dictionary to anonymize
            preserve_fields: Fields to keep (for statistical purposes)
            
        Returns:
            Anonymized data
        """
        preserve = preserve_fields or ['gender', 'birthDate', 'city', 'state']
        
        # Fields to remove completely
        remove_fields = [
            'name', 'identifier', 'telecom', 'address', 'photo',
            'contact', 'communication', 'generalPractitioner',
            'managingOrganization', 'link', 'cpf', 'email', 'phone'
        ]
        
        anonymized = {}
        
        for key, value in data.items():
            if key in remove_fields:
                continue
            elif key in preserve:
                # Keep but potentially generalize
                if key == 'birthDate' and value:
                    # Keep only year
                    anonymized[key] = value[:4] if len(value) >= 4 else None
                elif key == 'address' and isinstance(value, list):
                    # Keep only city/state
                    anonymized[key] = [
                        {'city': addr.get('city'), 'state': addr.get('state')}
                        for addr in value
                    ]
                else:
                    anonymized[key] = value
            elif isinstance(value, str):
                anonymized[key] = cls.anonymize_text(value)
            elif isinstance(value, dict):
                anonymized[key] = cls.anonymize_for_analytics(value, preserve)
            elif isinstance(value, list):
                anonymized[key] = [
                    cls.anonymize_for_analytics(item, preserve) 
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                anonymized[key] = value
        
        return anonymized
    
    @classmethod
    def validate_clinical_recommendation(
        cls,
        recommendation: str,
        patient_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate a clinical recommendation for bias.
        
        Args:
            recommendation: AI-generated recommendation
            patient_data: Patient context (optional)
            
        Returns:
            Validation result with status and any issues
        """
        issues = []
        
        # Check for biased terms
        has_bias, terms = cls.check_content_for_bias(recommendation, "clinical")
        if has_bias:
            issues.append({
                'type': 'biased_terms',
                'terms': terms,
                'severity': 'high'
            })
        
        # Check for demographic-based recommendations without clinical basis
        demographic_patterns = [
            r'por (ser|causa d[ae]|motivo d[ae]).*(negro|branco|pardo)',
            r'pacientes (negros|brancos|asian)',
            r'(homens|mulheres) (geralmente|normalmente|tipicamente)',
        ]
        
        for pattern in demographic_patterns:
            if re.search(pattern, recommendation, re.IGNORECASE):
                issues.append({
                    'type': 'demographic_generalization',
                    'pattern': pattern,
                    'severity': 'medium'
                })
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recommendation': recommendation if len(issues) == 0 else cls.sanitize_content(recommendation),
            'checked_at': datetime.now().isoformat()
        }
    
    @classmethod
    def _log_bias_detection(
        cls,
        content: str,
        terms: List[str],
        context: str
    ):
        """Log bias detection for audit."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'detected_terms': terms,
            'content_preview': content[:200] if len(content) > 200 else content,
            'action': 'flagged'
        }
        cls._bias_audit_log.append(log_entry)
        logger.warning(f"Bias detected: {terms} in context '{context}'")
    
    @classmethod
    def get_audit_log(
        cls,
        start_date: Optional[datetime] = None,
        context: Optional[str] = None
    ) -> List[Dict]:
        """Get bias detection audit log."""
        logs = cls._bias_audit_log.copy()
        
        if start_date:
            logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp']) >= start_date
            ]
        
        if context:
            logs = [log for log in logs if log['context'] == context]
        
        return logs
    
    @classmethod
    def generate_bias_report(cls) -> Dict[str, Any]:
        """
        Generate a bias detection summary report.
        """
        logs = cls._bias_audit_log
        
        if not logs:
            return {
                'total_detections': 0,
                'message': 'No bias detections recorded'
            }
        
        # Aggregate by term
        term_counts = {}
        for log in logs:
            for term in log['detected_terms']:
                term_counts[term] = term_counts.get(term, 0) + 1
        
        # Aggregate by context
        context_counts = {}
        for log in logs:
            ctx = log['context']
            context_counts[ctx] = context_counts.get(ctx, 0) + 1
        
        return {
            'total_detections': len(logs),
            'by_term': term_counts,
            'by_context': context_counts,
            'most_common_term': max(term_counts, key=term_counts.get) if term_counts else None,
            'generated_at': datetime.now().isoformat()
        }


# Singleton instance
_bias_prevention = None


def get_bias_prevention_service() -> BiasPreventionService:
    """Get bias prevention service singleton."""
    global _bias_prevention
    if _bias_prevention is None:
        _bias_prevention = BiasPreventionService()
    return _bias_prevention

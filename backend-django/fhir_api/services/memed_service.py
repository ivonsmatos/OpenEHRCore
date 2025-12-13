"""
e-Prescribing Service - MEMED Integration (Mockup)

Sprint 31: Receita Digital

Features:
- Prescription creation
- Drug database lookup
- ANVISA controlled substance validation
- Digital signature placeholder
- PDF generation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MEMEDService:
    """
    Mock MEMED integration for electronic prescribing.
    
    In production, this would integrate with MEMED API:
    https://memed.com.br
    """
    
    def __init__(self):
        self.api_url = "https://api.memed.com.br/v1"
        self.enabled = False  # Set to True with real API key
        self._load_drug_database()
    
    def _load_drug_database(self):
        """Load sample drug database."""
        self.drugs_db = [
            {"code": "1001", "name": "Amoxicilina 500mg", "presentation": "Cápsula", "class": "antibiotico", "controlled": False},
            {"code": "1002", "name": "Omeprazol 20mg", "presentation": "Cápsula", "class": "antiulceroso", "controlled": False},
            {"code": "1003", "name": "Losartana 50mg", "presentation": "Comprimido", "class": "anti-hipertensivo", "controlled": False},
            {"code": "1004", "name": "Metformina 850mg", "presentation": "Comprimido", "class": "antidiabetico", "controlled": False},
            {"code": "1005", "name": "Dipirona 1g", "presentation": "Comprimido", "class": "analgesico", "controlled": False},
            {"code": "1006", "name": "Ibuprofeno 600mg", "presentation": "Comprimido", "class": "antiinflamatorio", "controlled": False},
            {"code": "1007", "name": "Azitromicina 500mg", "presentation": "Comprimido", "class": "antibiotico", "controlled": False},
            {"code": "1008", "name": "Prednisona 20mg", "presentation": "Comprimido", "class": "corticoide", "controlled": False},
            {"code": "2001", "name": "Clonazepam 2mg", "presentation": "Comprimido", "class": "benzodiazepínico", "controlled": True, "anvisa_class": "B1"},
            {"code": "2002", "name": "Alprazolam 0.5mg", "presentation": "Comprimido", "class": "benzodiazepínico", "controlled": True, "anvisa_class": "B1"},
            {"code": "2003", "name": "Zolpidem 10mg", "presentation": "Comprimido", "class": "sedativo", "controlled": True, "anvisa_class": "B1"},
            {"code": "2004", "name": "Tramadol 50mg", "presentation": "Cápsula", "class": "opioide", "controlled": True, "anvisa_class": "A2"},
            {"code": "2005", "name": "Codeína 30mg", "presentation": "Comprimido", "class": "opioide", "controlled": True, "anvisa_class": "A1"},
        ]
    
    def search_drugs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search drugs in the database.
        
        Args:
            query: Search term (name or code)
            limit: Max results
        
        Returns:
            List of matching drugs
        """
        query_lower = query.lower()
        results = [
            drug for drug in self.drugs_db
            if query_lower in drug['name'].lower() or query_lower in drug['code']
        ]
        return results[:limit]
    
    def get_drug_by_code(self, code: str) -> Optional[Dict]:
        """Get drug by code."""
        for drug in self.drugs_db:
            if drug['code'] == code:
                return drug
        return None
    
    def create_prescription(
        self,
        patient_id: str,
        practitioner_id: str,
        items: List[Dict],
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an electronic prescription.
        
        Args:
            patient_id: Patient FHIR ID
            practitioner_id: Prescriber FHIR ID
            items: List of prescription items
            notes: Additional clinical notes
        
        Returns:
            Prescription result with ID and status
        """
        import uuid
        
        prescription_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # Validate items and check for controlled substances
        validated_items = []
        requires_special_form = False
        anvisa_classes = set()
        
        for item in items:
            drug_code = item.get('drug_code')
            drug = self.get_drug_by_code(drug_code)
            
            if not drug:
                return {
                    'success': False,
                    'error': f'Medicamento não encontrado: {drug_code}'
                }
            
            if drug.get('controlled'):
                requires_special_form = True
                anvisa_classes.add(drug.get('anvisa_class', 'B1'))
            
            validated_items.append({
                'drug_code': drug_code,
                'drug_name': drug['name'],
                'dosage': item.get('dosage', ''),
                'frequency': item.get('frequency', ''),
                'duration': item.get('duration', ''),
                'quantity': item.get('quantity', 1),
                'instructions': item.get('instructions', ''),
                'controlled': drug.get('controlled', False),
                'anvisa_class': drug.get('anvisa_class')
            })
        
        prescription = {
            'id': prescription_id,
            'status': 'active',
            'created_at': created_at,
            'patient_id': patient_id,
            'practitioner_id': practitioner_id,
            'items': validated_items,
            'notes': notes,
            'requires_special_form': requires_special_form,
            'anvisa_classes': list(anvisa_classes),
            'digital_signature': {
                'status': 'pending',
                'message': 'Assinatura digital necessária para validação'
            }
        }
        
        logger.info(f"Created prescription {prescription_id} for patient {patient_id}")
        
        return {
            'success': True,
            'prescription': prescription
        }
    
    def validate_anvisa(self, drug_code: str, patient_data: Dict) -> Dict[str, Any]:
        """
        Validate ANVISA rules for controlled substances.
        
        Args:
            drug_code: Drug code
            patient_data: Patient demographics
        
        Returns:
            Validation result
        """
        drug = self.get_drug_by_code(drug_code)
        
        if not drug:
            return {'valid': False, 'error': 'Medicamento não encontrado'}
        
        if not drug.get('controlled'):
            return {'valid': True, 'message': 'Medicamento não é controlado'}
        
        anvisa_class = drug.get('anvisa_class', 'B1')
        
        # Validation rules based on ANVISA class
        validations = []
        
        if anvisa_class in ['A1', 'A2']:
            validations.append({
                'rule': 'Receita amarela (Notificação A)',
                'required': True
            })
        elif anvisa_class == 'B1':
            validations.append({
                'rule': 'Receita azul (Notificação B)',
                'required': True
            })
        elif anvisa_class == 'B2':
            validations.append({
                'rule': 'Receita especial branca',
                'required': True
            })
        
        # Check patient age for certain drugs
        if patient_data.get('age') and patient_data.get('age') < 18:
            validations.append({
                'rule': 'Requer autorização responsável legal',
                'required': True
            })
        
        return {
            'valid': True,
            'drug': drug['name'],
            'anvisa_class': anvisa_class,
            'validations': validations,
            'requires_special_form': True
        }
    
    def generate_prescription_pdf(self, prescription: Dict) -> Dict[str, Any]:
        """
        Generate PDF for prescription (placeholder).
        
        In production, would generate actual PDF with:
        - QR code for verification
        - Digital signature
        - ANVISA-compliant format
        """
        return {
            'success': True,
            'pdf_url': f"/prescriptions/{prescription['id']}/pdf",
            'format': 'A4',
            'pages': 1,
            'includes_signature': prescription.get('digital_signature', {}).get('status') == 'signed'
        }
    
    def sign_prescription(self, prescription_id: str, provider_certificate: str) -> Dict[str, Any]:
        """
        Digitally sign a prescription (placeholder).
        
        In production, would use:
        - ICP-Brasil certificate
        - CFM/CRM validation
        - Timestamp authority
        """
        return {
            'success': True,
            'prescription_id': prescription_id,
            'signature': {
                'status': 'signed',
                'algorithm': 'RSA-SHA256',
                'timestamp': datetime.utcnow().isoformat(),
                'certificate_issuer': 'ICP-Brasil (Mock)',
                'valid_until': '2025-12-31T23:59:59Z'
            }
        }


# Singleton instance
_memed_service = None


def get_memed_service() -> MEMEDService:
    """Get MEMED service singleton."""
    global _memed_service
    if _memed_service is None:
        _memed_service = MEMEDService()
    return _memed_service

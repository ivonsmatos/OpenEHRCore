"""
Formulary Service - Advanced Medication Catalog

Sprint 36: Enhanced Formulary with MedicationKnowledge

Features:
- MedicationKnowledge FHIR resource
- RxNorm term types (SCD, SBD, GPCK, BPCK)
- Brand vs generic relationships
- Formulary by payor/insurance
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MedicationCode:
    """Medication coding."""
    system: str
    code: str
    display: str
    term_type: Optional[str] = None  # SCD, SBD, GPCK, BPCK, SCDG, SBDG


@dataclass
class MedicationIngredient:
    """Active ingredient."""
    name: str
    strength: str
    unit: str


@dataclass
class MedicationKnowledge:
    """FHIR MedicationKnowledge resource."""
    id: str
    code: MedicationCode
    status: str = "active"
    manufacturer: Optional[str] = None
    dose_form: Optional[str] = None
    amount: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    ingredients: List[MedicationIngredient] = field(default_factory=list)
    product_type: str = "generic"  # generic, brand
    related_medication: Optional[str] = None  # Related brand/generic
    packaging: Optional[str] = None
    regulatory_schedule: Optional[str] = None  # controlled substance schedule
    
    def to_fhir(self) -> Dict[str, Any]:
        """Convert to FHIR MedicationKnowledge resource."""
        resource = {
            "resourceType": "MedicationKnowledge",
            "id": self.id,
            "code": {
                "coding": [{
                    "system": self.code.system,
                    "code": self.code.code,
                    "display": self.code.display
                }]
            },
            "status": self.status,
            "productType": [{
                "coding": [{
                    "code": self.product_type,
                    "display": "Generic" if self.product_type == "generic" else "Brand"
                }]
            }]
        }
        
        if self.dose_form:
            resource["doseForm"] = {
                "coding": [{
                    "display": self.dose_form
                }]
            }
        
        if self.manufacturer:
            resource["manufacturer"] = {"display": self.manufacturer}
        
        if self.amount:
            resource["amount"] = {"value": self.amount}
        
        if self.synonyms:
            resource["synonym"] = self.synonyms
        
        if self.ingredients:
            resource["ingredient"] = [
                {
                    "itemCodeableConcept": {"text": ing.name},
                    "strength": {
                        "numerator": {
                            "value": float(ing.strength) if ing.strength.replace('.','').isdigit() else 0,
                            "unit": ing.unit
                        }
                    }
                }
                for ing in self.ingredients
            ]
        
        if self.related_medication:
            resource["relatedMedicationKnowledge"] = [{
                "type": {"text": "brand" if self.product_type == "generic" else "generic"},
                "reference": [{
                    "reference": f"MedicationKnowledge/{self.related_medication}"
                }]
            }]
        
        if self.regulatory_schedule:
            resource["regulatorySchedule"] = [{
                "schedule": {"coding": [{"code": self.regulatory_schedule}]}
            }]
        
        return resource


class FormularyService:
    """
    Advanced Formulary Service.
    
    Manages MedicationKnowledge resources for a comprehensive drug catalog.
    """
    
    # In-memory storage
    _medications: Dict[str, MedicationKnowledge] = {}
    _formularies: Dict[str, List[str]] = {}  # payor_id -> [medication_ids]
    
    @classmethod
    def _init_medications(cls):
        """Initialize built-in medications."""
        if cls._medications:
            return
        
        medications = [
            # Generics (SCD)
            MedicationKnowledge(
                id="amoxicilina-500",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "308182", "amoxicillin 500 MG Oral Capsule", "SCD"),
                dose_form="Capsule",
                amount="500 MG",
                product_type="generic",
                ingredients=[MedicationIngredient("Amoxicilina", "500", "mg")],
                packaging="Caixa com 21 cápsulas"
            ),
            MedicationKnowledge(
                id="amoxil-500",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "791953", "Amoxil 500 MG Oral Capsule", "SBD"),
                dose_form="Capsule",
                amount="500 MG",
                product_type="brand",
                manufacturer="GSK",
                related_medication="amoxicilina-500",
                ingredients=[MedicationIngredient("Amoxicilina", "500", "mg")]
            ),
            MedicationKnowledge(
                id="losartana-50",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "979467", "losartan potassium 50 MG Oral Tablet", "SCD"),
                dose_form="Tablet",
                amount="50 MG",
                product_type="generic",
                ingredients=[MedicationIngredient("Losartana Potássica", "50", "mg")],
                packaging="Caixa com 30 comprimidos"
            ),
            MedicationKnowledge(
                id="cozaar-50",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "979484", "Cozaar 50 MG Oral Tablet", "SBD"),
                dose_form="Tablet",
                amount="50 MG",
                product_type="brand",
                manufacturer="Merck",
                related_medication="losartana-50",
                ingredients=[MedicationIngredient("Losartana Potássica", "50", "mg")]
            ),
            MedicationKnowledge(
                id="metformina-850",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "861007", "metformin hydrochloride 850 MG Oral Tablet", "SCD"),
                dose_form="Tablet",
                amount="850 MG",
                product_type="generic",
                ingredients=[MedicationIngredient("Cloridrato de Metformina", "850", "mg")],
                packaging="Caixa com 30 comprimidos"
            ),
            MedicationKnowledge(
                id="glifage-850",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "861021", "Glucophage 850 MG Oral Tablet", "SBD"),
                dose_form="Tablet",
                amount="850 MG",
                product_type="brand",
                manufacturer="Merck",
                related_medication="metformina-850",
                ingredients=[MedicationIngredient("Cloridrato de Metformina", "850", "mg")]
            ),
            MedicationKnowledge(
                id="omeprazol-20",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "198106", "omeprazole 20 MG Delayed Release Oral Capsule", "SCD"),
                dose_form="Capsule",
                amount="20 MG",
                product_type="generic",
                ingredients=[MedicationIngredient("Omeprazol", "20", "mg")],
                packaging="Caixa com 28 cápsulas"
            ),
            MedicationKnowledge(
                id="clonazepam-2",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "197527", "clonazepam 2 MG Oral Tablet", "SCD"),
                dose_form="Tablet",
                amount="2 MG",
                product_type="generic",
                regulatory_schedule="B1",
                ingredients=[MedicationIngredient("Clonazepam", "2", "mg")],
                packaging="Caixa com 30 comprimidos"
            ),
            MedicationKnowledge(
                id="rivotril-2",
                code=MedicationCode("http://www.nlm.nih.gov/research/umls/rxnorm", "308047", "Klonopin 2 MG Oral Tablet", "SBD"),
                dose_form="Tablet",
                amount="2 MG",
                product_type="brand",
                manufacturer="Roche",
                regulatory_schedule="B1",
                related_medication="clonazepam-2",
                ingredients=[MedicationIngredient("Clonazepam", "2", "mg")]
            ),
            MedicationKnowledge(
                id="dipirona-500",
                code=MedicationCode("http://openehrcore.com.br/medications", "DIP500", "dipirona 500 MG Oral Tablet"),
                dose_form="Tablet",
                amount="500 MG",
                product_type="generic",
                ingredients=[MedicationIngredient("Dipirona Sódica", "500", "mg")],
                packaging="Caixa com 20 comprimidos"
            ),
        ]
        
        for med in medications:
            cls._medications[med.id] = med
        
        # Default formulary (all medications)
        cls._formularies["default"] = list(cls._medications.keys())
        
        # SUS formulary (only generics)
        cls._formularies["SUS"] = [
            med_id for med_id, med in cls._medications.items()
            if med.product_type == "generic"
        ]
        
        logger.info(f"Initialized {len(cls._medications)} medications")
    
    @classmethod
    def list_medications(
        cls,
        search: Optional[str] = None,
        product_type: Optional[str] = None,
        formulary_id: Optional[str] = None
    ) -> List[Dict]:
        """List medications with optional filters."""
        cls._init_medications()
        
        medications = list(cls._medications.values())
        
        # Filter by formulary
        if formulary_id and formulary_id in cls._formularies:
            allowed_ids = cls._formularies[formulary_id]
            medications = [m for m in medications if m.id in allowed_ids]
        
        # Filter by product type
        if product_type:
            medications = [m for m in medications if m.product_type == product_type]
        
        # Search
        if search:
            search_lower = search.lower()
            medications = [
                m for m in medications
                if search_lower in m.code.display.lower()
                or search_lower in m.id.lower()
            ]
        
        return [
            {
                "id": m.id,
                "code": m.code.code,
                "display": m.code.display,
                "product_type": m.product_type,
                "dose_form": m.dose_form,
                "manufacturer": m.manufacturer,
                "regulatory_schedule": m.regulatory_schedule
            }
            for m in medications
        ]
    
    @classmethod
    def get_medication(cls, medication_id: str) -> Optional[MedicationKnowledge]:
        """Get medication by ID."""
        cls._init_medications()
        return cls._medications.get(medication_id)
    
    @classmethod
    def get_medication_fhir(cls, medication_id: str) -> Optional[Dict]:
        """Get medication as FHIR resource."""
        med = cls.get_medication(medication_id)
        return med.to_fhir() if med else None
    
    @classmethod
    def get_alternatives(cls, medication_id: str) -> List[Dict]:
        """Get generic/brand alternatives for a medication."""
        cls._init_medications()
        
        med = cls._medications.get(medication_id)
        if not med:
            return []
        
        alternatives = []
        
        # Get related medication
        if med.related_medication:
            related = cls._medications.get(med.related_medication)
            if related:
                alternatives.append({
                    "id": related.id,
                    "display": related.code.display,
                    "product_type": related.product_type,
                    "relationship": "generic" if med.product_type == "brand" else "brand"
                })
        
        # Find medications that reference this one
        for other_id, other in cls._medications.items():
            if other.related_medication == medication_id:
                alternatives.append({
                    "id": other.id,
                    "display": other.code.display,
                    "product_type": other.product_type,
                    "relationship": "brand" if other.product_type == "brand" else "generic"
                })
        
        return alternatives
    
    @classmethod
    def list_formularies(cls) -> List[Dict]:
        """List available formularies."""
        cls._init_medications()
        
        return [
            {
                "id": form_id,
                "medication_count": len(med_ids)
            }
            for form_id, med_ids in cls._formularies.items()
        ]
    
    @classmethod
    def get_formulary(cls, formulary_id: str) -> Dict[str, Any]:
        """Get a specific formulary with its medications."""
        cls._init_medications()
        
        if formulary_id not in cls._formularies:
            return None
        
        med_ids = cls._formularies[formulary_id]
        medications = [
            cls._medications[mid].to_fhir()
            for mid in med_ids
            if mid in cls._medications
        ]
        
        return {
            "id": formulary_id,
            "medication_count": len(medications),
            "medications": medications
        }


# Singleton
_formulary_service = None


def get_formulary_service() -> FormularyService:
    """Get formulary service singleton."""
    global _formulary_service
    if _formulary_service is None:
        _formulary_service = FormularyService()
        FormularyService._init_medications()
    return _formulary_service

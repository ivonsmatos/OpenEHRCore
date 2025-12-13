"""
ISO 13606-2 Archetype Service

Implements clinical archetype support for ISO 13606-2/openEHR compliance.

ISO 13606 Parts:
- Part 1: Reference Model
- Part 2: Archetype Interchange Specification (this service)
- Part 3: Reference Archetypes and Term Lists
- Part 4: Security Requirements
- Part 5: Interface Specification

This service provides:
- Clinical archetype definitions
- Terminology bindings (SNOMED-CT, LOINC, ICD-10)
- Data validation against archetypes
- Archetype-constrained data entry
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TerminologySystem(Enum):
    """Supported terminology systems."""
    SNOMED_CT = "http://snomed.info/sct"
    LOINC = "http://loinc.org"
    ICD_10 = "http://hl7.org/fhir/sid/icd-10"
    ICD_10_CM = "http://hl7.org/fhir/sid/icd-10-cm"
    RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
    CVX = "http://hl7.org/fhir/sid/cvx"  # Vaccine codes
    CPT = "http://www.ama-assn.org/go/cpt"  # Procedure codes


@dataclass
class TerminologyBinding:
    """Binding to an external terminology."""
    system: TerminologySystem
    code: str
    display: str
    version: Optional[str] = None


@dataclass
class ArchetypeConstraint:
    """Constraint on a data element."""
    path: str  # Path within the archetype
    min: Optional[int] = None  # Minimum occurrences
    max: Optional[int] = None  # Maximum occurrences (None = unbounded)
    data_type: Optional[str] = None  # Expected data type
    pattern: Optional[str] = None  # Regex pattern
    allowed_values: Optional[List[str]] = None  # Enumerated values
    terminology_binding: Optional[TerminologyBinding] = None
    

@dataclass
class ClinicalArchetype:
    """
    Clinical archetype definition (simplified ADL representation).
    
    In full ISO 13606-2, this would be parsed from ADL files.
    Here we define common archetypes programmatically.
    """
    archetype_id: str  # e.g., "openEHR-EHR-OBSERVATION.blood_pressure.v2"
    concept: str  # Human-readable name
    description: str
    rm_type: str  # Reference Model type (OBSERVATION, EVALUATION, etc.)
    lifecycle_state: str = "published"
    version: str = "1.0.0"
    original_author: str = "OpenEHRCore"
    constraints: List[ArchetypeConstraint] = field(default_factory=list)
    terminology_bindings: List[TerminologyBinding] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'archetype_id': self.archetype_id,
            'concept': self.concept,
            'description': self.description,
            'rm_type': self.rm_type,
            'lifecycle_state': self.lifecycle_state,
            'version': self.version,
            'constraints': [
                {
                    'path': c.path,
                    'min': c.min,
                    'max': c.max,
                    'data_type': c.data_type,
                    'pattern': c.pattern,
                    'allowed_values': c.allowed_values,
                    'terminology': {
                        'system': c.terminology_binding.system.value,
                        'code': c.terminology_binding.code,
                        'display': c.terminology_binding.display
                    } if c.terminology_binding else None
                }
                for c in self.constraints
            ],
            'terminology_bindings': [
                {
                    'system': tb.system.value,
                    'code': tb.code,
                    'display': tb.display
                }
                for tb in self.terminology_bindings
            ]
        }


class ISO13606ArchetypeService:
    """
    ISO 13606-2 Archetype Service.
    
    Provides:
    - Pre-defined clinical archetypes
    - Data validation against archetypes
    - Terminology binding
    - FHIR resource mapping
    """
    
    # Pre-defined clinical archetypes (would be loaded from ADL files in production)
    ARCHETYPES: Dict[str, ClinicalArchetype] = {}
    
    @classmethod
    def _init_archetypes(cls):
        """Initialize built-in archetypes."""
        if cls.ARCHETYPES:
            return
        
        # =====================================================
        # VITAL SIGNS ARCHETYPES
        # =====================================================
        
        cls.ARCHETYPES["blood_pressure"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.blood_pressure.v2",
            concept="Pressão Arterial",
            description="Medição da pressão arterial sistólica e diastólica",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/systolic",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "8480-6",
                        "Systolic blood pressure"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/diastolic",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "8462-4",
                        "Diastolic blood pressure"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/position",
                    min=0, max=1,
                    data_type="CodeableConcept",
                    allowed_values=["sitting", "standing", "lying", "reclining"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "75367002", "Blood pressure")
            ]
        )
        
        cls.ARCHETYPES["body_temperature"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.body_temperature.v2",
            concept="Temperatura Corporal",
            description="Medição da temperatura corporal do paciente",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/temperature",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "8310-5",
                        "Body temperature"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/body_site",
                    min=0, max=1,
                    data_type="CodeableConcept",
                    allowed_values=["oral", "axillary", "rectal", "tympanic", "temporal"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "386725007", "Body temperature")
            ]
        )
        
        cls.ARCHETYPES["heart_rate"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.pulse.v2",
            concept="Frequência Cardíaca",
            description="Medição da frequência cardíaca/pulso",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/rate",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "8867-4",
                        "Heart rate"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/regularity",
                    min=0, max=1,
                    data_type="CodeableConcept",
                    allowed_values=["regular", "irregular"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "364075005", "Heart rate")
            ]
        )
        
        cls.ARCHETYPES["respiratory_rate"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.respiration.v2",
            concept="Frequência Respiratória",
            description="Medição da frequência respiratória",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/rate",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "9279-1",
                        "Respiratory rate"
                    )
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "86290005", "Respiratory rate")
            ]
        )
        
        cls.ARCHETYPES["oxygen_saturation"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.pulse_oximetry.v1",
            concept="Saturação de Oxigênio",
            description="Medição da saturação de oxigênio no sangue",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/spo2",
                    min=1, max=1,
                    data_type="Quantity",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "2708-6",
                        "Oxygen saturation in Arterial blood"
                    )
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "431314004", "SpO2")
            ]
        )
        
        # =====================================================
        # CLINICAL ARCHETYPES
        # =====================================================
        
        cls.ARCHETYPES["problem_diagnosis"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-EVALUATION.problem_diagnosis.v1",
            concept="Diagnóstico/Problema",
            description="Registro de um diagnóstico ou problema de saúde",
            rm_type="EVALUATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/problem_name",
                    min=1, max=1,
                    data_type="CodeableConcept",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.ICD_10,
                        "*",
                        "Any ICD-10 code"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/clinical_status",
                    min=1, max=1,
                    data_type="code",
                    allowed_values=["active", "recurrence", "relapse", "inactive", "remission", "resolved"]
                ),
                ArchetypeConstraint(
                    path="/data/verification_status",
                    min=0, max=1,
                    data_type="code",
                    allowed_values=["unconfirmed", "provisional", "differential", "confirmed", "refuted", "entered-in-error"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.ICD_10, "*", "ICD-10 diagnosis codes"),
                TerminologyBinding(TerminologySystem.SNOMED_CT, "*", "SNOMED-CT clinical findings")
            ]
        )
        
        cls.ARCHETYPES["medication_order"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-INSTRUCTION.medication_order.v3",
            concept="Prescrição de Medicamento",
            description="Ordem para administração de um medicamento",
            rm_type="INSTRUCTION",
            constraints=[
                ArchetypeConstraint(
                    path="/activities/medication_item",
                    min=1, max=1,
                    data_type="CodeableConcept",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.RXNORM,
                        "*",
                        "RxNorm medication code"
                    )
                ),
                ArchetypeConstraint(
                    path="/activities/dose",
                    min=1, max=1,
                    data_type="Quantity"
                ),
                ArchetypeConstraint(
                    path="/activities/route",
                    min=0, max=1,
                    data_type="CodeableConcept",
                    allowed_values=["oral", "sublingual", "intravenous", "intramuscular", "subcutaneous", "topical", "rectal", "inhalation"]
                ),
                ArchetypeConstraint(
                    path="/activities/frequency",
                    min=0, max=1,
                    data_type="string"
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.RXNORM, "*", "RxNorm drug codes")
            ]
        )
        
        cls.ARCHETYPES["laboratory_result"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-OBSERVATION.laboratory_test_result.v1",
            concept="Resultado Laboratorial",
            description="Resultado de um exame laboratorial",
            rm_type="OBSERVATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/test_name",
                    min=1, max=1,
                    data_type="CodeableConcept",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.LOINC,
                        "*",
                        "LOINC laboratory code"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/result_value",
                    min=1, max=1,
                    data_type="Quantity"
                ),
                ArchetypeConstraint(
                    path="/data/reference_range",
                    min=0, max=1,
                    data_type="Range"
                ),
                ArchetypeConstraint(
                    path="/data/interpretation",
                    min=0, max=1,
                    data_type="code",
                    allowed_values=["normal", "abnormal", "low", "high", "critical"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.LOINC, "*", "LOINC codes")
            ]
        )
        
        cls.ARCHETYPES["allergy_intolerance"] = ClinicalArchetype(
            archetype_id="openEHR-EHR-EVALUATION.adverse_reaction_risk.v1",
            concept="Alergia/Intolerância",
            description="Registro de alergias e intolerâncias do paciente",
            rm_type="EVALUATION",
            constraints=[
                ArchetypeConstraint(
                    path="/data/substance",
                    min=1, max=1,
                    data_type="CodeableConcept",
                    terminology_binding=TerminologyBinding(
                        TerminologySystem.SNOMED_CT,
                        "*",
                        "SNOMED-CT substance"
                    )
                ),
                ArchetypeConstraint(
                    path="/data/category",
                    min=0, max=1,
                    data_type="code",
                    allowed_values=["food", "medication", "environment", "biologic"]
                ),
                ArchetypeConstraint(
                    path="/data/criticality",
                    min=0, max=1,
                    data_type="code",
                    allowed_values=["low", "high", "unable-to-assess"]
                )
            ],
            terminology_bindings=[
                TerminologyBinding(TerminologySystem.SNOMED_CT, "*", "SNOMED-CT allergens")
            ]
        )
        
        logger.info(f"Initialized {len(cls.ARCHETYPES)} clinical archetypes")
    
    @classmethod
    def get_archetype(cls, archetype_name: str) -> Optional[ClinicalArchetype]:
        """
        Get an archetype by name.
        """
        cls._init_archetypes()
        return cls.ARCHETYPES.get(archetype_name)
    
    @classmethod
    def list_archetypes(cls, rm_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available archetypes.
        """
        cls._init_archetypes()
        
        archetypes = list(cls.ARCHETYPES.values())
        
        if rm_type:
            archetypes = [a for a in archetypes if a.rm_type == rm_type]
        
        return [
            {
                'archetype_id': a.archetype_id,
                'concept': a.concept,
                'rm_type': a.rm_type,
                'version': a.version
            }
            for a in archetypes
        ]
    
    @classmethod
    def validate_data(
        cls,
        archetype_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data against an archetype.
        
        Args:
            archetype_name: Name of the archetype
            data: Data dictionary to validate
            
        Returns:
            Validation result with errors if any
        """
        cls._init_archetypes()
        
        archetype = cls.ARCHETYPES.get(archetype_name)
        if not archetype:
            return {
                'valid': False,
                'errors': [f"Unknown archetype: {archetype_name}"]
            }
        
        errors = []
        warnings = []
        
        for constraint in archetype.constraints:
            path_parts = constraint.path.strip('/').split('/')
            value = data
            
            # Navigate to the path
            for part in path_parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            # Check required
            if constraint.min and constraint.min > 0 and value is None:
                errors.append(f"Required field missing: {constraint.path}")
            
            # Check allowed values
            if value and constraint.allowed_values:
                if value not in constraint.allowed_values:
                    errors.append(
                        f"Invalid value at {constraint.path}: {value}. "
                        f"Allowed: {constraint.allowed_values}"
                    )
            
            # Check pattern
            if value and constraint.pattern:
                import re
                if not re.match(constraint.pattern, str(value)):
                    errors.append(f"Value at {constraint.path} does not match pattern")
        
        return {
            'valid': len(errors) == 0,
            'archetype': archetype_name,
            'errors': errors,
            'warnings': warnings,
            'validated_at': datetime.now().isoformat()
        }
    
    @classmethod
    def map_to_fhir(
        cls,
        archetype_name: str,
        data: Dict[str, Any],
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Map archetype-constrained data to FHIR resource.
        
        Args:
            archetype_name: Archetype name
            data: Archetype-valid data
            patient_id: Patient ID for FHIR reference
            
        Returns:
            FHIR resource
        """
        archetype = cls.ARCHETYPES.get(archetype_name)
        if not archetype:
            raise ValueError(f"Unknown archetype: {archetype_name}")
        
        # Map RM type to FHIR resource type
        rm_to_fhir = {
            'OBSERVATION': 'Observation',
            'EVALUATION': 'Condition',
            'INSTRUCTION': 'MedicationRequest',
            'ACTION': 'Procedure'
        }
        
        fhir_type = rm_to_fhir.get(archetype.rm_type, 'Basic')
        
        fhir_resource = {
            'resourceType': fhir_type,
            'status': 'final' if fhir_type == 'Observation' else 'active',
            'subject': {'reference': f'Patient/{patient_id}'},
            'meta': {
                'profile': [f'http://openehrcore.com.br/fhir/StructureDefinition/{archetype_name}'],
                'tag': [{
                    'system': 'http://openehrcore.com.br/fhir/archetype',
                    'code': archetype.archetype_id
                }]
            }
        }
        
        # Add terminology binding as code
        if archetype.terminology_bindings:
            tb = archetype.terminology_bindings[0]
            fhir_resource['code'] = {
                'coding': [{
                    'system': tb.system.value,
                    'code': tb.code,
                    'display': tb.display
                }],
                'text': archetype.concept
            }
        
        # Add recorded timestamp
        fhir_resource['effectiveDateTime'] = datetime.now().isoformat()
        
        return fhir_resource
    
    @classmethod
    def get_terminology_codes(
        cls,
        system: TerminologySystem,
        search_term: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get terminology codes (stub - would connect to terminology server).
        
        In production, this would query a FHIR terminology server.
        """
        # Common LOINC codes for vital signs
        loinc_codes = [
            {"code": "8480-6", "display": "Systolic blood pressure"},
            {"code": "8462-4", "display": "Diastolic blood pressure"},
            {"code": "8867-4", "display": "Heart rate"},
            {"code": "9279-1", "display": "Respiratory rate"},
            {"code": "8310-5", "display": "Body temperature"},
            {"code": "2708-6", "display": "Oxygen saturation"},
            {"code": "29463-7", "display": "Body weight"},
            {"code": "8302-2", "display": "Body height"},
            {"code": "39156-5", "display": "BMI"},
            {"code": "2339-0", "display": "Glucose"},
        ]
        
        if system == TerminologySystem.LOINC:
            codes = loinc_codes
        else:
            codes = []
        
        if search_term:
            search_lower = search_term.lower()
            codes = [c for c in codes if search_lower in c['display'].lower()]
        
        return codes


# Singleton instance
_archetype_service = None


def get_archetype_service() -> ISO13606ArchetypeService:
    """Get archetype service singleton."""
    global _archetype_service
    if _archetype_service is None:
        _archetype_service = ISO13606ArchetypeService()
        ISO13606ArchetypeService._init_archetypes()
    return _archetype_service

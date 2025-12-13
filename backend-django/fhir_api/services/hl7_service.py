"""
HL7 v2.x Integration Service

Sprint 36: HL7 ADT and ORM/ORU Support

Features:
- HL7 v2.x message parsing
- ADT message generation (A01, A02, A03, A04, A08)
- ORM order messages
- ORU result messages
- FHIR-to-HL7 conversion
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class HL7MessageType(Enum):
    """HL7 message types."""
    # ADT Messages
    ADT_A01 = "ADT^A01"  # Admit
    ADT_A02 = "ADT^A02"  # Transfer
    ADT_A03 = "ADT^A03"  # Discharge
    ADT_A04 = "ADT^A04"  # Register
    ADT_A08 = "ADT^A08"  # Update patient info
    ADT_A11 = "ADT^A11"  # Cancel admit
    
    # Order Messages
    ORM_O01 = "ORM^O01"  # Order
    
    # Result Messages
    ORU_R01 = "ORU^R01"  # Observation result


class ADTEventType(Enum):
    """ADT event types."""
    ADMIT = "A01"
    TRANSFER = "A02"
    DISCHARGE = "A03"
    REGISTER = "A04"
    UPDATE = "A08"
    CANCEL_ADMIT = "A11"


@dataclass
class HL7Segment:
    """HL7 segment representation."""
    name: str
    fields: List[str]
    
    def to_string(self) -> str:
        """Convert segment to HL7 string."""
        return f"{self.name}|{'|'.join(self.fields)}"
    
    @classmethod
    def from_string(cls, segment_str: str) -> 'HL7Segment':
        """Parse segment from HL7 string."""
        parts = segment_str.split('|')
        return cls(name=parts[0], fields=parts[1:] if len(parts) > 1 else [])


@dataclass
class HL7Message:
    """HL7 v2.x message representation."""
    message_type: str
    segments: List[HL7Segment] = field(default_factory=list)
    
    def to_string(self) -> str:
        """Convert message to HL7 string format."""
        return '\r'.join(seg.to_string() for seg in self.segments)
    
    @classmethod
    def from_string(cls, message_str: str) -> 'HL7Message':
        """Parse HL7 message from string."""
        lines = message_str.replace('\n', '\r').split('\r')
        lines = [l for l in lines if l.strip()]
        
        segments = [HL7Segment.from_string(line) for line in lines]
        
        # Extract message type from MSH
        message_type = ""
        for seg in segments:
            if seg.name == "MSH" and len(seg.fields) >= 8:
                message_type = seg.fields[7]  # MSH-9
                break
        
        return cls(message_type=message_type, segments=segments)
    
    def get_segment(self, name: str) -> Optional[HL7Segment]:
        """Get first segment by name."""
        for seg in self.segments:
            if seg.name == name:
                return seg
        return None
    
    def get_segments(self, name: str) -> List[HL7Segment]:
        """Get all segments by name."""
        return [seg for seg in self.segments if seg.name == name]


class HL7Service:
    """
    HL7 v2.x Integration Service.
    
    Handles parsing, generation, and FHIR conversion of HL7 messages.
    """
    
    FIELD_SEPARATOR = "|"
    COMPONENT_SEPARATOR = "^"
    SUBCOMPONENT_SEPARATOR = "&"
    REPETITION_SEPARATOR = "~"
    ESCAPE_CHARACTER = "\\"
    
    @classmethod
    def create_msh_segment(
        cls,
        message_type: str,
        sending_app: str = "OPENEHRCORE",
        sending_facility: str = "HOSPITAL",
        receiving_app: str = "",
        receiving_facility: str = ""
    ) -> HL7Segment:
        """Create MSH (Message Header) segment."""
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        control_id = f"OEC{now}"
        
        return HL7Segment("MSH", [
            f"{cls.COMPONENT_SEPARATOR}{cls.REPETITION_SEPARATOR}{cls.ESCAPE_CHARACTER}{cls.SUBCOMPONENT_SEPARATOR}",
            sending_app,
            sending_facility,
            receiving_app,
            receiving_facility,
            now,
            "",  # Security
            message_type,
            control_id,
            "P",  # Processing ID (P=Production)
            "2.5.1"  # Version
        ])
    
    @classmethod
    def create_pid_segment(cls, patient: Dict[str, Any]) -> HL7Segment:
        """
        Create PID (Patient Identification) segment from FHIR Patient.
        """
        # Extract patient data
        patient_id = patient.get("id", "")
        
        # Name
        names = patient.get("name", [{}])
        name = names[0] if names else {}
        family = name.get("family", "")
        given = name.get("given", [""])
        given_name = given[0] if given else ""
        full_name = f"{family}^{given_name}"
        
        # Identifiers
        identifiers = patient.get("identifier", [])
        cpf = ""
        for ident in identifiers:
            if "cpf" in ident.get("system", "").lower():
                cpf = ident.get("value", "")
                break
        
        # Birth date
        birth_date = patient.get("birthDate", "").replace("-", "")
        
        # Gender
        gender_map = {"male": "M", "female": "F", "other": "O", "unknown": "U"}
        gender = gender_map.get(patient.get("gender", ""), "U")
        
        # Address
        addresses = patient.get("address", [{}])
        addr = addresses[0] if addresses else {}
        street = "^".join(addr.get("line", []))
        city = addr.get("city", "")
        state = addr.get("state", "")
        postal = addr.get("postalCode", "")
        address = f"{street}^^{city}^{state}^{postal}^BRA"
        
        # Phone
        telecoms = patient.get("telecom", [])
        phone = ""
        for tel in telecoms:
            if tel.get("system") == "phone":
                phone = tel.get("value", "")
                break
        
        return HL7Segment("PID", [
            "1",  # Set ID
            patient_id,  # External ID
            f"{patient_id}^^^OPENEHRCORE",  # Internal ID
            cpf,  # Alternate ID
            full_name,  # Patient Name
            "",  # Mother's maiden name
            birth_date,  # DOB
            gender,  # Sex
            "",  # Patient Alias
            "",  # Race (removed for anti-bias compliance)
            address,  # Address
            "",  # County
            phone,  # Phone
            "",  # Business phone
            "",  # Language
            "",  # Marital status
            "",  # Religion
            "",  # Patient Account Number
            "",  # SSN
        ])
    
    @classmethod
    def create_pv1_segment(
        cls,
        patient_class: str = "I",  # I=Inpatient, O=Outpatient, E=Emergency
        visit_number: str = "",
        attending_doctor: str = ""
    ) -> HL7Segment:
        """Create PV1 (Patient Visit) segment."""
        admit_date = datetime.now().strftime("%Y%m%d%H%M%S")
        
        return HL7Segment("PV1", [
            "1",  # Set ID
            patient_class,
            "",  # Assigned location
            "",  # Admission type
            "",  # Preadmit number
            "",  # Prior location
            attending_doctor,  # Attending doctor
            "",  # Referring doctor
            "",  # Consulting doctor
            "",  # Hospital service
            "",  # Temporary location
            "",  # Preadmit test indicator
            "",  # Re-admission indicator
            "",  # Admit source
            "",  # Ambulatory status
            "",  # VIP indicator
            "",  # Admitting doctor
            "",  # Patient type
            visit_number,  # Visit number
            "",  # Financial class
            "",  # Charge price indicator
            "",  # Courtesy code
            "",  # Credit rating
            "",  # Contract dates
            "",  # Contract amount
            "",  # Contract period
            "",  # Interest code
            "",  # Transfer to bad debt code
            "",  # Transfer to bad debt date
            "",  # Bad debt agency code
            "",  # Bad debt transfer amount
            "",  # Bad debt recovery amount
            "",  # Delete account indicator
            "",  # Delete account date
            "",  # Discharge disposition
            "",  # Discharged to location
            "",  # Diet type
            "",  # Servicing facility
            "",  # Bed status
            "",  # Account status
            "",  # Pending location
            "",  # Prior temporary location
            admit_date,  # Admit date/time
        ])
    
    @classmethod
    def create_adt_message(
        cls,
        patient: Dict[str, Any],
        event_type: ADTEventType,
        encounter: Optional[Dict[str, Any]] = None
    ) -> HL7Message:
        """
        Create an ADT message from FHIR resources.
        
        Args:
            patient: FHIR Patient resource
            event_type: ADT event type
            encounter: Optional FHIR Encounter resource
            
        Returns:
            HL7Message ready to send
        """
        message_type = f"ADT^{event_type.value}"
        
        segments = [
            cls.create_msh_segment(message_type),
            HL7Segment("EVN", [event_type.value, datetime.now().strftime("%Y%m%d%H%M%S")]),
            cls.create_pid_segment(patient),
        ]
        
        # Add PV1 if encounter provided
        if encounter:
            patient_class = "I" if encounter.get("class", {}).get("code") == "IMP" else "O"
            visit_number = encounter.get("id", "")
            segments.append(cls.create_pv1_segment(patient_class, visit_number))
        else:
            segments.append(cls.create_pv1_segment())
        
        return HL7Message(message_type=message_type, segments=segments)
    
    @classmethod
    def parse_adt_to_fhir(cls, message: HL7Message) -> Dict[str, Any]:
        """
        Parse ADT message to FHIR resources.
        
        Returns dict with 'patient' and optionally 'encounter'.
        """
        result = {}
        
        # Parse PID
        pid = message.get_segment("PID")
        if pid and len(pid.fields) >= 5:
            name_parts = pid.fields[4].split("^") if len(pid.fields) > 4 else ["", ""]
            
            patient = {
                "resourceType": "Patient",
                "id": pid.fields[2].split("^")[0] if len(pid.fields) > 2 else "",
                "name": [{
                    "family": name_parts[0] if name_parts else "",
                    "given": [name_parts[1]] if len(name_parts) > 1 else []
                }],
                "gender": {"M": "male", "F": "female", "O": "other"}.get(
                    pid.fields[7] if len(pid.fields) > 7 else "", "unknown"
                ),
                "birthDate": cls._parse_hl7_date(pid.fields[6]) if len(pid.fields) > 6 else None
            }
            
            result["patient"] = patient
        
        # Parse PV1 for encounter
        pv1 = message.get_segment("PV1")
        if pv1 and len(pv1.fields) >= 2:
            encounter_class = {
                "I": {"code": "IMP", "display": "Inpatient"},
                "O": {"code": "AMB", "display": "Ambulatory"},
                "E": {"code": "EMER", "display": "Emergency"}
            }.get(pv1.fields[1], {"code": "AMB", "display": "Ambulatory"})
            
            encounter = {
                "resourceType": "Encounter",
                "id": pv1.fields[18] if len(pv1.fields) > 18 else "",
                "class": encounter_class,
                "status": "in-progress",
                "subject": {"reference": f"Patient/{result.get('patient', {}).get('id', '')}"}
            }
            
            result["encounter"] = encounter
        
        return result
    
    @classmethod
    def _parse_hl7_date(cls, date_str: str) -> Optional[str]:
        """Convert HL7 date format to FHIR."""
        if not date_str or len(date_str) < 8:
            return None
        
        year = date_str[0:4]
        month = date_str[4:6]
        day = date_str[6:8]
        
        return f"{year}-{month}-{day}"
    
    @classmethod
    def create_orm_message(
        cls,
        service_request: Dict[str, Any],
        patient: Dict[str, Any]
    ) -> HL7Message:
        """
        Create ORM^O01 order message from FHIR ServiceRequest.
        """
        message_type = "ORM^O01"
        
        # Build ORC segment (Common Order)
        order_id = service_request.get("id", "")
        order_control = "NW"  # New order
        
        orc = HL7Segment("ORC", [
            order_control,
            order_id,  # Placer order number
            "",  # Filler order number
            "",  # Placer group number
            "SC",  # Order status (SC = scheduled)
        ])
        
        # Build OBR segment (Observation Request)
        code = service_request.get("code", {}).get("coding", [{}])[0]
        test_code = code.get("code", "")
        test_name = code.get("display", "")
        
        obr = HL7Segment("OBR", [
            "1",  # Set ID
            order_id,  # Placer order number
            "",  # Filler order number
            f"{test_code}^{test_name}",  # Universal service ID
            "R",  # Priority (R = routine)
            datetime.now().strftime("%Y%m%d%H%M%S"),  # Requested date/time
        ])
        
        segments = [
            cls.create_msh_segment(message_type),
            cls.create_pid_segment(patient),
            orc,
            obr
        ]
        
        return HL7Message(message_type=message_type, segments=segments)
    
    @classmethod
    def parse_oru_to_fhir(cls, message: HL7Message) -> List[Dict[str, Any]]:
        """
        Parse ORU^R01 result message to FHIR Observations.
        """
        observations = []
        
        # Get patient ID from PID
        pid = message.get_segment("PID")
        patient_id = ""
        if pid and len(pid.fields) > 2:
            patient_id = pid.fields[2].split("^")[0]
        
        # Parse OBX segments
        obx_segments = message.get_segments("OBX")
        
        for obx in obx_segments:
            if len(obx.fields) < 5:
                continue
            
            set_id = obx.fields[0]
            value_type = obx.fields[1]
            observation_id = obx.fields[2].split("^")
            
            obs_code = observation_id[0] if observation_id else ""
            obs_display = observation_id[1] if len(observation_id) > 1 else ""
            
            value = obx.fields[4] if len(obx.fields) > 4 else ""
            units = obx.fields[5] if len(obx.fields) > 5 else ""
            
            observation = {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": obs_code,
                        "display": obs_display
                    }]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectiveDateTime": datetime.now().isoformat()
            }
            
            # Set value based on type
            if value_type == "NM":  # Numeric
                try:
                    observation["valueQuantity"] = {
                        "value": float(value),
                        "unit": units.split("^")[0] if units else ""
                    }
                except ValueError:
                    observation["valueString"] = value
            else:
                observation["valueString"] = value
            
            observations.append(observation)
        
        return observations


# Singleton
_hl7_service = None


def get_hl7_service() -> HL7Service:
    """Get HL7 service singleton."""
    global _hl7_service
    if _hl7_service is None:
        _hl7_service = HL7Service()
    return _hl7_service

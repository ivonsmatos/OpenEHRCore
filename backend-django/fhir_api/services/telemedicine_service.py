"""
Telemedicine Service

Sprint 37: Brazil Essential Integrations

Features:
- Video consultation rooms
- Session management
- Recording (optional)
- Integration with FHIR Encounter
- CFM Telemedicina compliance
"""

import logging
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Telemedicine session status."""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ParticipantRole(Enum):
    """Participant roles in teleconsultation."""
    PRACTITIONER = "practitioner"
    PATIENT = "patient"
    OBSERVER = "observer"


@dataclass
class Participant:
    """Session participant."""
    id: str
    role: ParticipantRole
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    joined_at: Optional[str] = None
    left_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "name": self.name,
            "email": self.email,
            "joined_at": self.joined_at,
            "left_at": self.left_at
        }


@dataclass
class TelemedicineSession:
    """Telemedicine session representation."""
    id: str
    scheduled_start: str
    scheduled_end: str
    status: SessionStatus = SessionStatus.SCHEDULED
    patient_id: str = ""
    practitioner_id: str = ""
    encounter_id: Optional[str] = None
    room_url: Optional[str] = None
    patient_url: Optional[str] = None
    practitioner_url: Optional[str] = None
    participants: List[Participant] = field(default_factory=list)
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    recording_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "scheduled_start": self.scheduled_start,
            "scheduled_end": self.scheduled_end,
            "status": self.status.value,
            "patient_id": self.patient_id,
            "practitioner_id": self.practitioner_id,
            "encounter_id": self.encounter_id,
            "room_url": self.room_url,
            "patient_url": self.patient_url,
            "practitioner_url": self.practitioner_url,
            "participants": [p.to_dict() for p in self.participants],
            "actual_start": self.actual_start,
            "actual_end": self.actual_end,
            "duration_minutes": self.duration_minutes,
            "created_at": self.created_at
        }


class TelemedicineService:
    """
    Telemedicine Service for Video Consultations.
    
    Supports multiple providers:
    - Jitsi Meet (self-hosted)
    - Daily.co
    - Whereby
    - Twilio Video
    
    Compliant with CFM Resolution 2.314/2022.
    """
    
    # Configuration
    PROVIDER = "jitsi"  # jitsi, daily, whereby, twilio
    BASE_URL = "https://meet.jit.si"  # Default to public Jitsi
    API_KEY = ""
    SECRET_KEY = ""
    
    # Session storage
    _sessions: Dict[str, TelemedicineSession] = {}
    
    @classmethod
    def configure(
        cls,
        provider: str = "jitsi",
        base_url: str = None,
        api_key: str = None,
        secret_key: str = None
    ):
        """Configure telemedicine provider."""
        cls.PROVIDER = provider
        if base_url:
            cls.BASE_URL = base_url
        if api_key:
            cls.API_KEY = api_key
        if secret_key:
            cls.SECRET_KEY = secret_key
    
    @classmethod
    def create_session(
        cls,
        patient_id: str,
        practitioner_id: str,
        scheduled_start: datetime,
        duration_minutes: int = 30,
        patient_name: str = "Paciente",
        practitioner_name: str = "Médico",
        encounter_id: Optional[str] = None
    ) -> TelemedicineSession:
        """
        Create a new telemedicine session.
        
        Args:
            patient_id: Patient FHIR ID
            practitioner_id: Practitioner FHIR ID
            scheduled_start: Scheduled start time
            duration_minutes: Expected duration
            patient_name: Patient display name
            practitioner_name: Practitioner display name
            encounter_id: Optional linked FHIR Encounter
            
        Returns:
            TelemedicineSession with room URLs
        """
        session_id = str(uuid.uuid4())[:12].upper()
        
        # Calculate end time
        scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
        
        # Generate room
        room_name = f"consulta-{session_id}"
        
        # Generate URLs based on provider
        urls = cls._generate_room_urls(room_name, patient_name, practitioner_name)
        
        # Create participants
        participants = [
            Participant(
                id=patient_id,
                role=ParticipantRole.PATIENT,
                name=patient_name
            ),
            Participant(
                id=practitioner_id,
                role=ParticipantRole.PRACTITIONER,
                name=practitioner_name
            )
        ]
        
        session = TelemedicineSession(
            id=session_id,
            scheduled_start=scheduled_start.isoformat(),
            scheduled_end=scheduled_end.isoformat(),
            patient_id=patient_id,
            practitioner_id=practitioner_id,
            encounter_id=encounter_id,
            room_url=urls["room"],
            patient_url=urls["patient"],
            practitioner_url=urls["practitioner"],
            participants=participants
        )
        
        cls._sessions[session_id] = session
        
        logger.info(f"Telemedicine session created: {session_id}")
        
        return session
    
    @classmethod
    def _generate_room_urls(
        cls,
        room_name: str,
        patient_name: str,
        practitioner_name: str
    ) -> Dict[str, str]:
        """Generate room URLs based on provider."""
        
        if cls.PROVIDER == "jitsi":
            base = f"{cls.BASE_URL}/{room_name}"
            return {
                "room": base,
                "patient": f"{base}#userInfo.displayName=%22{patient_name}%22",
                "practitioner": f"{base}#userInfo.displayName=%22{practitioner_name}%22&config.startWithAudioMuted=false&config.startWithVideoMuted=false"
            }
        
        elif cls.PROVIDER == "daily":
            # Daily.co would require API call to create room
            base = f"https://openehrcore.daily.co/{room_name}"
            return {
                "room": base,
                "patient": f"{base}?t={cls._generate_token(patient_name, 'patient')}",
                "practitioner": f"{base}?t={cls._generate_token(practitioner_name, 'owner')}"
            }
        
        elif cls.PROVIDER == "whereby":
            base = f"https://whereby.com/{room_name}"
            return {
                "room": base,
                "patient": base,
                "practitioner": f"{base}?roomKey=host"
            }
        
        else:
            # Default to simple room URL
            return {
                "room": f"{cls.BASE_URL}/{room_name}",
                "patient": f"{cls.BASE_URL}/{room_name}",
                "practitioner": f"{cls.BASE_URL}/{room_name}"
            }
    
    @classmethod
    def _generate_token(cls, name: str, role: str) -> str:
        """Generate JWT token for authenticated access."""
        # Simplified token - in production use proper JWT
        payload = f"{name}:{role}:{datetime.now().timestamp()}"
        if cls.SECRET_KEY:
            signature = hmac.new(
                cls.SECRET_KEY.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            return f"{signature}"
        return hashlib.md5(payload.encode()).hexdigest()[:16]
    
    @classmethod
    def start_session(cls, session_id: str, started_by: str) -> Optional[TelemedicineSession]:
        """Start a telemedicine session."""
        session = cls._sessions.get(session_id)
        if not session:
            return None
        
        session.status = SessionStatus.IN_PROGRESS
        session.actual_start = datetime.now().isoformat()
        
        # Update participant joined time
        for p in session.participants:
            if p.id == started_by:
                p.joined_at = datetime.now().isoformat()
        
        logger.info(f"Telemedicine session started: {session_id}")
        
        return session
    
    @classmethod
    def join_session(cls, session_id: str, participant_id: str) -> Optional[TelemedicineSession]:
        """Record participant joining session."""
        session = cls._sessions.get(session_id)
        if not session:
            return None
        
        for p in session.participants:
            if p.id == participant_id:
                p.joined_at = datetime.now().isoformat()
        
        # If first join, mark as waiting
        if session.status == SessionStatus.SCHEDULED:
            session.status = SessionStatus.WAITING
        
        return session
    
    @classmethod
    def end_session(
        cls,
        session_id: str,
        notes: Optional[str] = None
    ) -> Optional[TelemedicineSession]:
        """End a telemedicine session."""
        session = cls._sessions.get(session_id)
        if not session:
            return None
        
        session.status = SessionStatus.COMPLETED
        session.actual_end = datetime.now().isoformat()
        session.notes = notes
        
        # Calculate duration
        if session.actual_start:
            start = datetime.fromisoformat(session.actual_start)
            end = datetime.fromisoformat(session.actual_end)
            session.duration_minutes = int((end - start).total_seconds() / 60)
        
        # Update participant left times
        for p in session.participants:
            if p.joined_at and not p.left_at:
                p.left_at = session.actual_end
        
        logger.info(f"Telemedicine session ended: {session_id} ({session.duration_minutes} min)")
        
        return session
    
    @classmethod
    def cancel_session(cls, session_id: str, reason: str = None) -> Optional[TelemedicineSession]:
        """Cancel a scheduled session."""
        session = cls._sessions.get(session_id)
        if not session:
            return None
        
        if session.status in [SessionStatus.COMPLETED, SessionStatus.IN_PROGRESS]:
            return None  # Can't cancel completed or in-progress
        
        session.status = SessionStatus.CANCELLED
        session.notes = reason
        
        logger.info(f"Telemedicine session cancelled: {session_id}")
        
        return session
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[TelemedicineSession]:
        """Get session by ID."""
        return cls._sessions.get(session_id)
    
    @classmethod
    def list_sessions(
        cls,
        patient_id: Optional[str] = None,
        practitioner_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List sessions with filters."""
        sessions = list(cls._sessions.values())
        
        if patient_id:
            sessions = [s for s in sessions if s.patient_id == patient_id]
        
        if practitioner_id:
            sessions = [s for s in sessions if s.practitioner_id == practitioner_id]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        if date_from:
            sessions = [s for s in sessions if datetime.fromisoformat(s.scheduled_start) >= date_from]
        
        if date_to:
            sessions = [s for s in sessions if datetime.fromisoformat(s.scheduled_start) <= date_to]
        
        sessions.sort(key=lambda s: s.scheduled_start, reverse=True)
        
        return [s.to_dict() for s in sessions[:limit]]
    
    @classmethod
    def get_upcoming_sessions(cls, practitioner_id: str, hours: int = 24) -> List[Dict]:
        """Get upcoming sessions for a practitioner."""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        sessions = [
            s for s in cls._sessions.values()
            if s.practitioner_id == practitioner_id
            and s.status == SessionStatus.SCHEDULED
            and now <= datetime.fromisoformat(s.scheduled_start) <= cutoff
        ]
        
        sessions.sort(key=lambda s: s.scheduled_start)
        
        return [s.to_dict() for s in sessions]
    
    @classmethod
    def to_fhir_encounter(cls, session: TelemedicineSession) -> Dict[str, Any]:
        """Convert session to FHIR Encounter resource."""
        status_map = {
            SessionStatus.SCHEDULED: "planned",
            SessionStatus.WAITING: "arrived",
            SessionStatus.IN_PROGRESS: "in-progress",
            SessionStatus.COMPLETED: "finished",
            SessionStatus.CANCELLED: "cancelled",
            SessionStatus.NO_SHOW: "cancelled"
        }
        
        encounter = {
            "resourceType": "Encounter",
            "id": session.encounter_id or session.id,
            "status": status_map.get(session.status, "planned"),
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "VR",
                "display": "Virtual"
            },
            "type": [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "448337001",
                    "display": "Telemedicine consultation"
                }]
            }],
            "subject": {"reference": f"Patient/{session.patient_id}"},
            "participant": [
                {
                    "type": [{"coding": [{"code": "PPRF", "display": "Primary performer"}]}],
                    "individual": {"reference": f"Practitioner/{session.practitioner_id}"}
                }
            ],
            "period": {
                "start": session.actual_start or session.scheduled_start,
                "end": session.actual_end or session.scheduled_end
            }
        }
        
        if session.duration_minutes:
            encounter["length"] = {
                "value": session.duration_minutes,
                "unit": "minutes",
                "system": "http://unitsofmeasure.org",
                "code": "min"
            }
        
        return encounter


# Singleton
_telemedicine_service = None


def get_telemedicine_service() -> TelemedicineService:
    """Get telemedicine service singleton."""
    global _telemedicine_service
    if _telemedicine_service is None:
        _telemedicine_service = TelemedicineService()
    return _telemedicine_service

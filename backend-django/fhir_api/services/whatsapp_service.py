"""
WhatsApp Business Integration Service

Sprint 37: Brazil Essential Integrations

Features:
- Send appointment reminders
- Send lab results notifications
- Send medication reminders
- Receive patient responses
- Template message support
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WhatsApp message types."""
    TEXT = "text"
    TEMPLATE = "template"
    DOCUMENT = "document"
    IMAGE = "image"


class TemplateType(Enum):
    """Pre-approved template types."""
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    LAB_RESULT_READY = "lab_result_ready"
    MEDICATION_REMINDER = "medication_reminder"
    PRESCRIPTION_SENT = "prescription_sent"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    TELECONSULT_LINK = "teleconsult_link"


@dataclass
class WhatsAppMessage:
    """WhatsApp message representation."""
    id: str
    to: str  # Phone number with country code
    type: MessageType
    template: Optional[TemplateType] = None
    content: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    status: str = "pending"  # pending, sent, delivered, read, failed
    patient_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "to": self.to,
            "type": self.type.value,
            "template": self.template.value if self.template else None,
            "content": self.content,
            "variables": self.variables,
            "status": self.status,
            "patient_id": self.patient_id,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "delivered_at": self.delivered_at
        }


class WhatsAppService:
    """
    WhatsApp Business API Integration.
    
    Supports both Cloud API (Meta) and on-premise API.
    """
    
    # Configuration
    API_URL = "https://graph.facebook.com/v18.0"
    PHONE_NUMBER_ID = ""
    ACCESS_TOKEN = ""
    BUSINESS_ACCOUNT_ID = ""
    
    # Message storage
    _messages: Dict[str, WhatsAppMessage] = {}
    
    # Pre-approved templates (must be approved by Meta)
    TEMPLATES = {
        TemplateType.APPOINTMENT_REMINDER: {
            "name": "consulta_lembrete",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Olá {{1}}! Lembramos da sua consulta em {{2}} às {{3}} com {{4}}."}
            ]
        },
        TemplateType.APPOINTMENT_CONFIRMATION: {
            "name": "consulta_confirmada",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Sua consulta foi confirmada! {{1}} em {{2}} às {{3}}."}
            ]
        },
        TemplateType.LAB_RESULT_READY: {
            "name": "resultado_exame",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Olá {{1}}! Seu resultado de {{2}} já está disponível. Acesse: {{3}}"}
            ]
        },
        TemplateType.MEDICATION_REMINDER: {
            "name": "lembrete_medicamento",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Hora de tomar {{1}}. Dose: {{2}}."}
            ]
        },
        TemplateType.PRESCRIPTION_SENT: {
            "name": "receita_enviada",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Sua receita foi enviada! Medicamento: {{1}}. Acesse: {{2}}"}
            ]
        },
        TemplateType.PAYMENT_CONFIRMATION: {
            "name": "pagamento_confirmado",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Pagamento de R$ {{1}} confirmado! Referente a: {{2}}. Obrigado!"}
            ]
        },
        TemplateType.TELECONSULT_LINK: {
            "name": "teleconsulta_link",
            "language": "pt_BR",
            "components": [
                {"type": "body", "text": "Sua teleconsulta começa em {{1}}. Acesse: {{2}}"}
            ]
        }
    }
    
    @classmethod
    def configure(cls, phone_number_id: str, access_token: str, business_id: str = None):
        """Configure WhatsApp API credentials."""
        cls.PHONE_NUMBER_ID = phone_number_id
        cls.ACCESS_TOKEN = access_token
        if business_id:
            cls.BUSINESS_ACCOUNT_ID = business_id
    
    @classmethod
    def send_template_message(
        cls,
        to: str,
        template: TemplateType,
        variables: List[str],
        patient_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """
        Send a pre-approved template message.
        
        Args:
            to: Phone number with country code (e.g., "5511999998888")
            template: Template type to use
            variables: List of variables to fill in template
            patient_id: Optional patient reference
            
        Returns:
            WhatsAppMessage with status
        """
        message_id = str(uuid.uuid4())
        
        # Format phone number
        phone = cls._format_phone(to)
        
        # Get template config
        template_config = cls.TEMPLATES.get(template, {})
        
        # Build message
        message = WhatsAppMessage(
            id=message_id,
            to=phone,
            type=MessageType.TEMPLATE,
            template=template,
            content=template_config.get("components", [{}])[0].get("text", ""),
            variables={f"var{i+1}": v for i, v in enumerate(variables)},
            patient_id=patient_id
        )
        
        # In production, this would call the WhatsApp API
        # For now, simulate sending
        try:
            cls._send_to_api(message, template_config)
            message.status = "sent"
            message.sent_at = datetime.now().isoformat()
            logger.info(f"WhatsApp message sent: {message_id} to {phone}")
        except Exception as e:
            message.status = "failed"
            message.error = str(e)
            logger.error(f"WhatsApp message failed: {message_id} - {e}")
        
        # Store message
        cls._messages[message_id] = message
        
        return message
    
    @classmethod
    def send_appointment_reminder(
        cls,
        patient_name: str,
        patient_phone: str,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str,
        patient_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send appointment reminder."""
        return cls.send_template_message(
            to=patient_phone,
            template=TemplateType.APPOINTMENT_REMINDER,
            variables=[patient_name, appointment_date, appointment_time, doctor_name],
            patient_id=patient_id
        )
    
    @classmethod
    def send_lab_result_notification(
        cls,
        patient_name: str,
        patient_phone: str,
        exam_name: str,
        result_url: str,
        patient_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send lab result ready notification."""
        return cls.send_template_message(
            to=patient_phone,
            template=TemplateType.LAB_RESULT_READY,
            variables=[patient_name, exam_name, result_url],
            patient_id=patient_id
        )
    
    @classmethod
    def send_medication_reminder(
        cls,
        patient_phone: str,
        medication_name: str,
        dosage: str,
        patient_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send medication reminder."""
        return cls.send_template_message(
            to=patient_phone,
            template=TemplateType.MEDICATION_REMINDER,
            variables=[medication_name, dosage],
            patient_id=patient_id
        )
    
    @classmethod
    def send_teleconsult_link(
        cls,
        patient_phone: str,
        start_time: str,
        meeting_url: str,
        patient_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send teleconsultation link."""
        return cls.send_template_message(
            to=patient_phone,
            template=TemplateType.TELECONSULT_LINK,
            variables=[start_time, meeting_url],
            patient_id=patient_id
        )
    
    @classmethod
    def _format_phone(cls, phone: str) -> str:
        """Format phone number for WhatsApp API."""
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Add Brazil country code if not present
        if len(digits) == 11:  # DDD + 9 digits
            digits = "55" + digits
        elif len(digits) == 10:  # Old format without 9
            digits = "55" + digits
        
        return digits
    
    @classmethod
    def _send_to_api(cls, message: WhatsAppMessage, template_config: Dict):
        """
        Send message to WhatsApp Cloud API.
        
        In production, this would make HTTP request to Meta's API.
        """
        if not cls.ACCESS_TOKEN or not cls.PHONE_NUMBER_ID:
            logger.warning("WhatsApp not configured - message simulated")
            return
        
        # API payload would be:
        # {
        #     "messaging_product": "whatsapp",
        #     "to": message.to,
        #     "type": "template",
        #     "template": {
        #         "name": template_config["name"],
        #         "language": {"code": template_config["language"]},
        #         "components": [...]
        #     }
        # }
        
        # For now, simulate success
        pass
    
    @classmethod
    def handle_webhook(cls, payload: Dict) -> Dict:
        """
        Handle incoming webhook from WhatsApp.
        
        Processes:
        - Message status updates
        - Incoming messages
        """
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Handle status updates
            statuses = value.get("statuses", [])
            for status in statuses:
                message_id = status.get("id")
                new_status = status.get("status")
                
                if message_id in cls._messages:
                    msg = cls._messages[message_id]
                    msg.status = new_status
                    
                    if new_status == "delivered":
                        msg.delivered_at = datetime.now().isoformat()
                    elif new_status == "read":
                        msg.read_at = datetime.now().isoformat()
            
            # Handle incoming messages
            messages = value.get("messages", [])
            for msg in messages:
                logger.info(f"Incoming WhatsApp message from {msg.get('from')}: {msg.get('text', {}).get('body')}")
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    def get_message(cls, message_id: str) -> Optional[WhatsAppMessage]:
        """Get message by ID."""
        return cls._messages.get(message_id)
    
    @classmethod
    def list_messages(
        cls,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List messages with optional filters."""
        messages = list(cls._messages.values())
        
        if patient_id:
            messages = [m for m in messages if m.patient_id == patient_id]
        
        if status:
            messages = [m for m in messages if m.status == status]
        
        messages.sort(key=lambda m: m.created_at, reverse=True)
        
        return [m.to_dict() for m in messages[:limit]]
    
    @classmethod
    def to_fhir_communication(cls, message: WhatsAppMessage) -> Dict[str, Any]:
        """Convert to FHIR Communication resource."""
        return {
            "resourceType": "Communication",
            "id": message.id,
            "status": "completed" if message.status in ["delivered", "read"] else "in-progress",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "notification",
                    "display": "Notification"
                }]
            }],
            "medium": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                    "code": "SMSWRIT",
                    "display": "SMS/WhatsApp"
                }]
            }],
            "subject": {"reference": f"Patient/{message.patient_id}"} if message.patient_id else None,
            "sent": message.sent_at,
            "received": message.delivered_at,
            "payload": [{
                "contentString": message.content
            }]
        }


# Singleton
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    """Get WhatsApp service singleton."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service

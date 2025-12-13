"""
PIX Payment Integration Service

Sprint 37: Brazil Essential Integrations

Features:
- PIX QR Code generation
- Payment status tracking
- Webhook handling for confirmations
- FHIR PaymentNotice resource
"""

import logging
import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PixPayment:
    """PIX payment representation."""
    id: str
    amount: float
    description: str
    payer_name: Optional[str] = None
    payer_cpf: Optional[str] = None
    merchant_name: str = "OpenEHRCore Clinic"
    merchant_city: str = "São Paulo"
    pix_key: str = ""
    expiration_minutes: int = 30
    status: str = "pending"  # pending, paid, expired, cancelled
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    paid_at: Optional[str] = None
    qr_code: Optional[str] = None
    qr_code_base64: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "description": self.description,
            "payer_name": self.payer_name,
            "payer_cpf": self.payer_cpf,
            "merchant_name": self.merchant_name,
            "merchant_city": self.merchant_city,
            "status": self.status,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "qr_code": self.qr_code,
            "expiration_minutes": self.expiration_minutes
        }


class PixService:
    """
    PIX Payment Service for Brazil.
    
    Implements:
    - EMV QR Code generation (BR Code)
    - Payment tracking
    - Webhook callbacks
    """
    
    # In-memory storage (use database in production)
    _payments: Dict[str, PixPayment] = {}
    
    # PIX configuration
    PIX_KEY_TYPE = "CNPJ"  # CPF, CNPJ, EMAIL, PHONE, EVP
    PIX_KEY = ""  # Set from environment
    MERCHANT_NAME = "OPENEHRCORE CLINICA"
    MERCHANT_CITY = "SAO PAULO"
    
    @classmethod
    def configure(cls, pix_key: str, merchant_name: str = None, merchant_city: str = None):
        """Configure PIX credentials."""
        cls.PIX_KEY = pix_key
        if merchant_name:
            cls.MERCHANT_NAME = merchant_name
        if merchant_city:
            cls.MERCHANT_CITY = merchant_city
    
    @classmethod
    def create_payment(
        cls,
        amount: float,
        description: str,
        payer_name: Optional[str] = None,
        payer_cpf: Optional[str] = None,
        reference_id: Optional[str] = None,
        expiration_minutes: int = 30
    ) -> PixPayment:
        """
        Create a new PIX payment.
        
        Args:
            amount: Payment amount in BRL
            description: Payment description
            payer_name: Optional payer name
            payer_cpf: Optional payer CPF
            reference_id: Optional external reference
            expiration_minutes: QR code expiration time
            
        Returns:
            PixPayment with QR code
        """
        payment_id = reference_id or str(uuid.uuid4())[:8].upper()
        
        payment = PixPayment(
            id=payment_id,
            amount=amount,
            description=description,
            payer_name=payer_name,
            payer_cpf=payer_cpf,
            merchant_name=cls.MERCHANT_NAME,
            merchant_city=cls.MERCHANT_CITY,
            pix_key=cls.PIX_KEY,
            expiration_minutes=expiration_minutes
        )
        
        # Generate EMV QR Code
        payment.qr_code = cls._generate_emv_code(payment)
        
        # Store payment
        cls._payments[payment_id] = payment
        
        logger.info(f"PIX payment created: {payment_id} - R$ {amount:.2f}")
        
        return payment
    
    @classmethod
    def _generate_emv_code(cls, payment: PixPayment) -> str:
        """
        Generate EMV QR Code (BR Code) for PIX.
        
        Format follows BACEN specification for static PIX.
        """
        def format_field(id: str, value: str) -> str:
            """Format EMV field: ID + Length + Value."""
            length = str(len(value)).zfill(2)
            return f"{id}{length}{value}"
        
        # Payload Format Indicator
        payload = format_field("00", "01")
        
        # Merchant Account Information (PIX)
        gui = format_field("00", "br.gov.bcb.pix")
        key = format_field("01", payment.pix_key or "pix@openehrcore.com.br")
        description = format_field("02", payment.description[:25])
        merchant_account = format_field("26", gui + key + description)
        payload += merchant_account
        
        # Merchant Category Code
        payload += format_field("52", "0000")
        
        # Transaction Currency (986 = BRL)
        payload += format_field("53", "986")
        
        # Transaction Amount
        amount_str = f"{payment.amount:.2f}"
        payload += format_field("54", amount_str)
        
        # Country Code
        payload += format_field("58", "BR")
        
        # Merchant Name
        payload += format_field("59", payment.merchant_name[:25])
        
        # Merchant City
        payload += format_field("60", payment.merchant_city[:15])
        
        # Additional Data Field (Transaction ID)
        txid = format_field("05", payment.id)
        payload += format_field("62", txid)
        
        # CRC16 placeholder
        payload += "6304"
        
        # Calculate CRC16-CCITT
        crc = cls._calculate_crc16(payload)
        payload = payload[:-4] + format_field("63", crc)
        
        return payload
    
    @classmethod
    def _calculate_crc16(cls, data: str) -> str:
        """Calculate CRC16-CCITT for EMV QR Code."""
        crc = 0xFFFF
        polynomial = 0x1021
        
        for byte in data.encode('utf-8'):
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFFFF
        
        return format(crc, '04X')
    
    @classmethod
    def get_payment(cls, payment_id: str) -> Optional[PixPayment]:
        """Get payment by ID."""
        return cls._payments.get(payment_id)
    
    @classmethod
    def list_payments(
        cls,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List payments with optional status filter."""
        payments = list(cls._payments.values())
        
        if status:
            payments = [p for p in payments if p.status == status]
        
        # Sort by creation date descending
        payments.sort(key=lambda p: p.created_at, reverse=True)
        
        return [p.to_dict() for p in payments[:limit]]
    
    @classmethod
    def confirm_payment(cls, payment_id: str, transaction_id: str = None) -> Optional[PixPayment]:
        """
        Confirm payment (called by webhook from bank).
        """
        payment = cls._payments.get(payment_id)
        if not payment:
            return None
        
        payment.status = "paid"
        payment.paid_at = datetime.now().isoformat()
        
        logger.info(f"PIX payment confirmed: {payment_id}")
        
        return payment
    
    @classmethod
    def cancel_payment(cls, payment_id: str) -> Optional[PixPayment]:
        """Cancel a pending payment."""
        payment = cls._payments.get(payment_id)
        if not payment or payment.status != "pending":
            return None
        
        payment.status = "cancelled"
        
        return payment
    
    @classmethod
    def check_expired_payments(cls):
        """Check and mark expired payments."""
        now = datetime.now()
        
        for payment in cls._payments.values():
            if payment.status == "pending":
                created = datetime.fromisoformat(payment.created_at)
                expiration = created + timedelta(minutes=payment.expiration_minutes)
                
                if now > expiration:
                    payment.status = "expired"
                    logger.info(f"PIX payment expired: {payment.id}")
    
    @classmethod
    def to_fhir_payment_notice(cls, payment: PixPayment) -> Dict[str, Any]:
        """Convert to FHIR PaymentNotice resource."""
        return {
            "resourceType": "PaymentNotice",
            "id": payment.id,
            "status": "active" if payment.status == "pending" else "cancelled",
            "created": payment.created_at,
            "payment": {
                "identifier": {
                    "system": "urn:pix:br",
                    "value": payment.id
                }
            },
            "amount": {
                "value": payment.amount,
                "currency": "BRL"
            },
            "paymentStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/paymentstatus",
                    "code": "paid" if payment.status == "paid" else "cleared"
                }]
            }
        }


# Singleton
_pix_service = None


def get_pix_service() -> PixService:
    """Get PIX service singleton."""
    global _pix_service
    if _pix_service is None:
        _pix_service = PixService()
    return _pix_service

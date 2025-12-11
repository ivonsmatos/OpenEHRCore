"""
Brazilian Healthcare Identifier Validators

Validates professional registration numbers for Brazilian healthcare professionals:
- CRM: Conselho Regional de Medicina (doctors)
- CRF: Conselho Regional de Farmácia (pharmacists)
- COREN: Conselho Regional de Enfermagem (nurses)
- CRO: Conselho Regional de Odontologia (dentists)
- CRP: Conselho Regional de Psicologia (psychologists)
- CREFITO: Conselho Regional de Fisioterapia e Terapia Ocupacional
"""
import re
from typing import Tuple, Optional, Dict

# Brazilian States (UF codes)
VALID_UF_CODES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Council prefix patterns
COUNCIL_PATTERNS = {
    'CRM': r'^CRM[-/]?([A-Z]{2})[-/]?(\d{4,7})$',
    'CRF': r'^CRF[-/]?([A-Z]{2})[-/]?(\d{4,6})$',
    'COREN': r'^COREN[-/]?([A-Z]{2})[-/]?(\d{4,7})$',
    'CRO': r'^CRO[-/]?([A-Z]{2})[-/]?(\d{4,6})$',
    'CRP': r'^CRP[-/]?(\d{2})[-/]?(\d{4,6})$',
    'CREFITO': r'^CREFITO[-/]?(\d{1,2})[-/]?(\d{4,6})[-/]?([FT])$',
}


def validate_crm(identifier: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CRM (Conselho Regional de Medicina) number.
    
    Format: CRM-UF-XXXXXX or CRM/UF/XXXXXX or CRMUFXXXXXX
    Example: CRM-SP-123456, CRM/RJ/54321, CRMMG123456
    
    Args:
        identifier: The CRM identifier to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    identifier = identifier.upper().strip()
    
    # Try different patterns
    patterns = [
        r'^CRM[-/]?([A-Z]{2})[-/]?(\d{4,7})$',  # CRM-SP-123456
        r'^(\d{4,7})[-/]?([A-Z]{2})[-/]?CRM$',  # 123456-SP-CRM (reverse)
        r'^(\d{4,7})[-/]?CRM[-/]?([A-Z]{2})$',  # 123456-CRM-SP
    ]
    
    for pattern in patterns:
        match = re.match(pattern, identifier)
        if match:
            groups = match.groups()
            # Determine which group is UF and which is number
            uf = None
            number = None
            for g in groups:
                if g.isalpha() and len(g) == 2:
                    uf = g
                elif g.isdigit():
                    number = g
            
            if uf and number:
                if uf not in VALID_UF_CODES:
                    return False, f"UF inválida: {uf}. UFs válidas são: {', '.join(VALID_UF_CODES)}"
                if len(number) < 4:
                    return False, f"Número CRM muito curto: {number}. Mínimo 4 dígitos."
                if len(number) > 7:
                    return False, f"Número CRM muito longo: {number}. Máximo 7 dígitos."
                return True, None
    
    return False, f"Formato CRM inválido: {identifier}. Use formato CRM-UF-NÚMERO (ex: CRM-SP-123456)"


def validate_crf(identifier: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CRF (Conselho Regional de Farmácia) number.
    
    Format: CRF-UF-XXXXX
    Example: CRF-SP-12345
    """
    identifier = identifier.upper().strip()
    
    match = re.match(r'^CRF[-/]?([A-Z]{2})[-/]?(\d{4,6})$', identifier)
    if match:
        uf, number = match.groups()
        if uf not in VALID_UF_CODES:
            return False, f"UF inválida: {uf}"
        return True, None
    
    return False, f"Formato CRF inválido: {identifier}. Use formato CRF-UF-NÚMERO (ex: CRF-SP-12345)"


def validate_coren(identifier: str) -> Tuple[bool, Optional[str]]:
    """
    Validate COREN (Conselho Regional de Enfermagem) number.
    
    Format: COREN-UF-XXXXXXX
    Example: COREN-SP-1234567
    
    Note: COREN may have suffix indicating category (ENF, TEC, AUX)
    """
    identifier = identifier.upper().strip()
    
    # Remove category suffix if present
    identifier = re.sub(r'[-/]?(ENF|TEC|AUX)$', '', identifier)
    
    match = re.match(r'^COREN[-/]?([A-Z]{2})[-/]?(\d{4,7})$', identifier)
    if match:
        uf, number = match.groups()
        if uf not in VALID_UF_CODES:
            return False, f"UF inválida: {uf}"
        return True, None
    
    return False, f"Formato COREN inválido: {identifier}. Use formato COREN-UF-NÚMERO (ex: COREN-SP-1234567)"


def validate_cro(identifier: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CRO (Conselho Regional de Odontologia) number.
    
    Format: CRO-UF-XXXXX
    Example: CRO-SP-12345
    """
    identifier = identifier.upper().strip()
    
    match = re.match(r'^CRO[-/]?([A-Z]{2})[-/]?(\d{4,6})$', identifier)
    if match:
        uf, number = match.groups()
        if uf not in VALID_UF_CODES:
            return False, f"UF inválida: {uf}"
        return True, None
    
    return False, f"Formato CRO inválido: {identifier}. Use formato CRO-UF-NÚMERO (ex: CRO-SP-12345)"


def validate_professional_identifier(identifier: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate any Brazilian professional healthcare identifier.
    
    Automatically detects the type and validates accordingly.
    
    Args:
        identifier: The identifier to validate
        
    Returns:
        Tuple of (is_valid, identifier_type, error_message)
    """
    identifier = identifier.upper().strip()
    
    if identifier.startswith('CRM'):
        is_valid, error = validate_crm(identifier)
        return is_valid, 'CRM', error
    elif identifier.startswith('CRF'):
        is_valid, error = validate_crf(identifier)
        return is_valid, 'CRF', error
    elif identifier.startswith('COREN'):
        is_valid, error = validate_coren(identifier)
        return is_valid, 'COREN', error
    elif identifier.startswith('CRO'):
        is_valid, error = validate_cro(identifier)
        return is_valid, 'CRO', error
    else:
        return False, 'UNKNOWN', f"Tipo de identificador não reconhecido. Prefixos válidos: CRM, CRF, COREN, CRO"


def format_identifier(identifier: str) -> str:
    """
    Format identifier to standard format.
    
    Example: CRMSP123456 -> CRM-SP-123456
    """
    identifier = identifier.upper().strip()
    
    # CRM
    match = re.match(r'^CRM[-/]?([A-Z]{2})[-/]?(\d+)$', identifier)
    if match:
        return f"CRM-{match.group(1)}-{match.group(2)}"
    
    # CRF
    match = re.match(r'^CRF[-/]?([A-Z]{2})[-/]?(\d+)$', identifier)
    if match:
        return f"CRF-{match.group(1)}-{match.group(2)}"
    
    # COREN
    match = re.match(r'^COREN[-/]?([A-Z]{2})[-/]?(\d+)([-/]?(ENF|TEC|AUX))?$', identifier)
    if match:
        base = f"COREN-{match.group(1)}-{match.group(2)}"
        if match.group(4):
            base += f"-{match.group(4)}"
        return base
    
    # CRO
    match = re.match(r'^CRO[-/]?([A-Z]{2})[-/]?(\d+)$', identifier)
    if match:
        return f"CRO-{match.group(1)}-{match.group(2)}"
    
    return identifier


# Medical Specialties (SNOMED CT based with CBOs)
MEDICAL_SPECIALTIES: Dict[str, Dict] = {
    '394802001': {'display': 'Medicina Geral', 'display_en': 'General Medicine', 'cbo': '225125'},
    '394579002': {'display': 'Cardiologia', 'display_en': 'Cardiology', 'cbo': '225120'},
    '394585009': {'display': 'Dermatologia', 'display_en': 'Dermatology', 'cbo': '225130'},
    '394582007': {'display': 'Psiquiatria', 'display_en': 'Psychiatry', 'cbo': '225133'},
    '394587001': {'display': 'Pediatria', 'display_en': 'Pediatrics', 'cbo': '225124'},
    '394577000': {'display': 'Anestesiologia', 'display_en': 'Anesthesiology', 'cbo': '225105'},
    '394802001': {'display': 'Clínica Médica', 'display_en': 'Internal Medicine', 'cbo': '225125'},
    '394584008': {'display': 'Ginecologia e Obstetrícia', 'display_en': 'Gynecology and Obstetrics', 'cbo': '225215'},
    '394576006': {'display': 'Cirurgia Geral', 'display_en': 'General Surgery', 'cbo': '225250'},
    '394609007': {'display': 'Neurologia', 'display_en': 'Neurology', 'cbo': '225122'},
    '394610002': {'display': 'Oncologia', 'display_en': 'Oncology', 'cbo': '225128'},
    '394579003': {'display': 'Ortopedia', 'display_en': 'Orthopedics', 'cbo': '225125'},
    '394593009': {'display': 'Urologia', 'display_en': 'Urology', 'cbo': '225136'},
    '394600006': {'display': 'Oftalmologia', 'display_en': 'Ophthalmology', 'cbo': '225265'},
    '394612005': {'display': 'Otorrinolaringologia', 'display_en': 'Otorhinolaryngology', 'cbo': '225270'},
    '394583002': {'display': 'Endocrinologia', 'display_en': 'Endocrinology', 'cbo': '225123'},
    '394591006': {'display': 'Gastroenterologia', 'display_en': 'Gastroenterology', 'cbo': '225135'},
    '394805004': {'display': 'Medicina de Emergência', 'display_en': 'Emergency Medicine', 'cbo': '225155'},
    '394594003': {'display': 'Pneumologia', 'display_en': 'Pulmonology', 'cbo': '225134'},
    '394821009': {'display': 'Reumatologia', 'display_en': 'Rheumatology', 'cbo': '225132'},
}


def get_all_specialties() -> list:
    """
    Returns list of all medical specialties for frontend dropdown.
    """
    return [
        {
            'code': code,
            'display': spec['display'],
            'display_en': spec['display_en'],
            'cbo': spec.get('cbo')
        }
        for code, spec in MEDICAL_SPECIALTIES.items()
    ]


def get_specialty_by_code(code: str) -> Optional[Dict]:
    """
    Get specialty details by SNOMED CT code.
    """
    spec = MEDICAL_SPECIALTIES.get(code)
    if spec:
        return {
            'code': code,
            **spec
        }
    return None

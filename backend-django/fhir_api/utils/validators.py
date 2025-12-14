"""
🔐 VALIDADORES DE DADOS - HEALTHSTACK EHR
============================================

Validações críticas para segurança e integridade de dados.
"""

import re
from typing import Union


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro com verificação de dígito verificador.
    
    Args:
        cpf: CPF com ou sem formatação (123.456.789-00 ou 12345678900)
    
    Returns:
        True se CPF é válido, False caso contrário
    
    Exemplos:
        >>> validate_cpf('123.456.789-09')
        True
        >>> validate_cpf('12345678909')
        True
        >>> validate_cpf('000.000.000-00')
        False
        >>> validate_cpf('111.111.111-11')
        False
    """
    # Remove formatação (pontos, traços, espaços)
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    # Verifica tamanho
    if len(cpf_limpo) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais (CPFs inválidos conhecidos)
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum((10 - i) * int(cpf_limpo[i]) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Verifica primeiro dígito
    if int(cpf_limpo[9]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum((11 - i) * int(cpf_limpo[i]) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica segundo dígito
    if int(cpf_limpo[10]) != digito2:
        return False
    
    return True


def validate_uuid(uuid_string: str) -> bool:
    """
    Valida se string é UUID válido (v4).
    
    Args:
        uuid_string: String para validar
    
    Returns:
        True se é UUID válido, False caso contrário
    
    Exemplo:
        >>> validate_uuid('550e8400-e29b-41d4-a716-446655440000')
        True
        >>> validate_uuid('invalid-uuid')
        False
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def validate_patient_id(patient_id: str) -> bool:
    """
    Valida se patient_id é válido (UUID ou ID numérico).
    
    Aceita:
    - UUID v4: '550e8400-e29b-41d4-a716-446655440000'
    - IDs numéricos: '1', '42', '12345'
    
    Rejeita:
    - Strings vazias
    - IDs com caracteres especiais (exceto hífens em UUID)
    - SQL injection attempts
    
    Args:
        patient_id: String para validar
    
    Returns:
        True se é ID válido, False caso contrário
    
    Exemplo:
        >>> validate_patient_id('550e8400-e29b-41d4-a716-446655440000')
        True
        >>> validate_patient_id('8')
        True
        >>> validate_patient_id('12345')
        True
        >>> validate_patient_id("'; DROP TABLE patients; --")
        False
    """
    if not patient_id or not isinstance(patient_id, str):
        return False
    
    # Remove espaços em branco
    patient_id = patient_id.strip()
    
    # Verifica se é UUID válido
    if validate_uuid(patient_id):
        return True
    
    # Verifica se é ID numérico válido (apenas dígitos, máximo 20 caracteres)
    if patient_id.isdigit() and 1 <= len(patient_id) <= 20:
        return True
    
    # Qualquer outro formato é inválido
    return False


def sanitize_cpf(cpf: str) -> str:
    """
    Remove formatação do CPF, mantendo apenas dígitos.
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        CPF apenas com dígitos (11 caracteres)
    
    Exemplo:
        >>> sanitize_cpf('123.456.789-09')
        '12345678909'
    """
    return ''.join(filter(str.isdigit, cpf))


def format_cpf(cpf: str) -> str:
    """
    Formata CPF para exibição (123.456.789-00).
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        CPF formatado com pontos e traço
    
    Exemplo:
        >>> format_cpf('12345678909')
        '123.456.789-09'
    """
    cpf_limpo = sanitize_cpf(cpf)
    
    if len(cpf_limpo) != 11:
        return cpf  # Retorna original se não tiver 11 dígitos
    
    return f"{cpf_limpo[0:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"


def validate_email(email: str) -> bool:
    """
    Valida formato de e-mail.
    
    Args:
        email: Endereço de e-mail
    
    Returns:
        True se formato é válido, False caso contrário
    """
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))


def sanitize_fhir_search_param(value: str) -> str:
    """
    Remove caracteres perigosos de parâmetros de busca FHIR.
    Previne injection attacks.
    
    Args:
        value: Parâmetro de busca
    
    Returns:
        Parâmetro sanitizado
    
    Exemplo:
        >>> sanitize_fhir_search_param("João'; DROP TABLE--")
        'João DROP TABLE'
    """
    # Permitir apenas alfanuméricos, espaços, hífens e acentos
    return re.sub(r'[^a-zA-Z0-9\s\-áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', '', value)


def validate_date_not_future(date_string: str) -> bool:
    """
    Valida que data não está no futuro (útil para data de nascimento).
    
    Args:
        date_string: Data no formato YYYY-MM-DD
    
    Returns:
        True se data é válida e não está no futuro
    """
    from datetime import datetime
    
    try:
        date = datetime.strptime(date_string, '%Y-%m-%d')
        return date <= datetime.now()
    except ValueError:
        return False


def calculate_age(birth_date: str) -> Union[int, None]:
    """
    Calcula idade a partir da data de nascimento.
    
    Args:
        birth_date: Data de nascimento no formato YYYY-MM-DD
    
    Returns:
        Idade em anos ou None se data inválida
    
    Exemplo:
        >>> calculate_age('1990-01-01')  # Em 2025
        35
    """
    from datetime import datetime
    
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.now()
        
        age = today.year - birth.year
        
        # Ajusta se ainda não fez aniversário este ano
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        
        # Validar que idade não é negativa (data futura)
        return age if age >= 0 else None
        
    except (ValueError, AttributeError):
        return None

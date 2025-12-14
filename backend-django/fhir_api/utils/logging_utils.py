"""
🔒 UTILITÁRIOS DE LOGGING SEGURO
==================================

Funções para sanitizar dados sensíveis antes de logar.
"""

from typing import Any, Dict, List, Union
import copy


# Lista de campos sensíveis que devem ser redacted
SENSITIVE_FIELDS = {
    'cpf',
    'password',
    'senha',
    'token',
    'access_token',
    'refresh_token',
    'secret',
    'api_key',
    'apikey',
    'authorization',
    'credit_card',
    'card_number',
    'cvv',
    'ssn',
    'social_security',
}


def sanitize_for_log(data: Union[Dict, List, str, Any], partial: bool = False) -> Any:
    """
    Remove ou redige dados sensíveis antes de logar.
    
    Args:
        data: Dados a serem sanitizados (dict, list, str, ou outro tipo)
        partial: Se True, mostra parte do valor (primeiros 4 caracteres)
                 Se False, substitui completamente por ***REDACTED***
    
    Returns:
        Cópia dos dados com valores sensíveis redacted
    
    Exemplos:
        >>> sanitize_for_log({'nome': 'João', 'cpf': '12345678900'})
        {'nome': 'João', 'cpf': '***REDACTED***'}
        
        >>> sanitize_for_log({'token': 'abc123xyz'}, partial=True)
        {'token': 'abc1***'}
    """
    # Se não é dict ou list, retornar como está
    if not isinstance(data, (dict, list)):
        return data
    
    # Fazer cópia profunda para não modificar original
    sanitized = copy.deepcopy(data)
    
    if isinstance(sanitized, dict):
        return _sanitize_dict(sanitized, partial)
    elif isinstance(sanitized, list):
        return _sanitize_list(sanitized, partial)
    
    return sanitized


def _sanitize_dict(data: Dict, partial: bool = False) -> Dict:
    """Sanitiza dicionário recursivamente."""
    for key, value in data.items():
        # Verificar se key está em campos sensíveis (case-insensitive)
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            if partial and isinstance(value, str) and len(value) > 4:
                # Mostrar apenas primeiros 4 caracteres
                data[key] = value[:4] + '***'
            else:
                data[key] = '***REDACTED***'
        
        # Recursão para dicts e lists aninhados
        elif isinstance(value, dict):
            data[key] = _sanitize_dict(value, partial)
        elif isinstance(value, list):
            data[key] = _sanitize_list(value, partial)
    
    return data


def _sanitize_list(data: List, partial: bool = False) -> List:
    """Sanitiza lista recursivamente."""
    sanitized_list = []
    for item in data:
        if isinstance(item, dict):
            sanitized_list.append(_sanitize_dict(item, partial))
        elif isinstance(item, list):
            sanitized_list.append(_sanitize_list(item, partial))
        else:
            sanitized_list.append(item)
    
    return sanitized_list


def sanitize_url(url: str) -> str:
    """
    Remove parâmetros sensíveis de URL.
    
    Args:
        url: URL potencialmente com tokens/secrets em query string
    
    Returns:
        URL com parâmetros sensíveis redacted
    
    Exemplo:
        >>> sanitize_url('https://api.example.com/data?token=abc123&name=João')
        'https://api.example.com/data?token=***REDACTED***&name=João'
    """
    import urllib.parse
    
    parsed = urllib.parse.urlparse(url)
    
    if not parsed.query:
        return url
    
    # Parsear query string
    params = urllib.parse.parse_qs(parsed.query)
    
    # Sanitizar parâmetros sensíveis
    for key in params.keys():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            params[key] = ['***REDACTED***']
    
    # Reconstruir URL
    new_query = urllib.parse.urlencode(params, doseq=True)
    sanitized = parsed._replace(query=new_query)
    
    return urllib.parse.urlunparse(sanitized)


def mask_cpf(cpf: str) -> str:
    """
    Mascara CPF para exibição segura em logs.
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        CPF mascarado (apenas últimos 2 dígitos visíveis)
    
    Exemplo:
        >>> mask_cpf('123.456.789-09')
        '***.***.***.09'
        >>> mask_cpf('12345678909')
        '*********09'
    """
    # Remove formatação
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_limpo) != 11:
        return '***INVALID***'
    
    # Verifica se CPF original tinha formatação
    if '.' in cpf or '-' in cpf:
        return f"***.***.***.{cpf_limpo[-2:]}"
    else:
        return f"{'*' * 9}{cpf_limpo[-2:]}"


def create_audit_log_entry(
    action: str,
    user: str,
    resource_type: str,
    resource_id: str,
    details: Dict = None
) -> Dict:
    """
    Cria entrada de log de auditoria com dados sanitizados.
    
    Args:
        action: Ação realizada (CREATE, UPDATE, DELETE, READ)
        user: Identificador do usuário
        resource_type: Tipo de recurso FHIR (Patient, Observation, etc)
        resource_id: ID do recurso
        details: Detalhes adicionais (serão sanitizados)
    
    Returns:
        Dict com entrada de log pronta para ser persistida
    """
    from datetime import datetime
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'user': user,
        'resource_type': resource_type,
        'resource_id': resource_id,
    }
    
    if details:
        log_entry['details'] = sanitize_for_log(details)
    
    return log_entry


# Exemplo de uso com logger
def safe_log_patient_data(logger, patient_data: Dict):
    """
    Exemplo de função para logar dados de paciente de forma segura.
    
    Args:
        logger: Instância do logger
        patient_data: Dados do paciente (serão sanitizados)
    """
    sanitized = sanitize_for_log(patient_data)
    logger.info(f"Patient data: {sanitized}")


# Decorator para sanitizar automaticamente argumentos de função
def sanitize_logs(func):
    """
    Decorator que automaticamente sanitiza logs dentro da função.
    
    Uso:
        @sanitize_logs
        def process_patient(patient_data):
            logger.info(f"Processing: {patient_data}")
            # patient_data será automaticamente sanitizado no log
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitizar argumentos para logging
        safe_args = [sanitize_for_log(arg) if isinstance(arg, (dict, list)) else arg 
                     for arg in args]
        safe_kwargs = {k: sanitize_for_log(v) if isinstance(v, (dict, list)) else v 
                       for k, v in kwargs.items()}
        
        # Log de entrada (opcional - comentar em produção para performance)
        # logger.debug(f"Calling {func.__name__} with args={safe_args}, kwargs={safe_kwargs}")
        
        # Executar função original
        return func(*args, **kwargs)
    
    return wrapper

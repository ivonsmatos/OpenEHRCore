"""
Configuration management for OpenEHRCore Agent.
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ServerConfig:
    """OpenEHRCore server configuration."""
    url: str = "http://localhost:8000"
    api_key: str = ""
    websocket_url: Optional[str] = None
    
    def __post_init__(self):
        if not self.websocket_url:
            # Derive WebSocket URL from HTTP URL
            ws_scheme = "wss" if self.url.startswith("https") else "ws"
            http_url = self.url.replace("https://", "").replace("http://", "")
            self.websocket_url = f"{ws_scheme}://{http_url}/ws/agent/"


@dataclass
class MLLPConfig:
    """MLLP server configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 2575
    timeout: int = 30
    max_message_size: int = 1048576  # 1MB


@dataclass
class DICOMConfig:
    """DICOM server configuration."""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 4242
    ae_title: str = "OPENEHRCORE"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = "agent.log"
    max_size_mb: int = 10
    backup_count: int = 5
    json_format: bool = True


@dataclass
class AgentConfig:
    """Main agent configuration."""
    server: ServerConfig = field(default_factory=ServerConfig)
    mllp: MLLPConfig = field(default_factory=MLLPConfig)
    dicom: DICOMConfig = field(default_factory=DICOMConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Agent identification
    agent_id: Optional[str] = None
    agent_name: str = "OpenEHRCore Agent"
    
    # Retry configuration
    reconnect_delay: int = 5  # seconds
    max_reconnect_attempts: int = 0  # 0 = infinite


def load_config(path: Path) -> AgentConfig:
    """
    Load configuration from YAML file.
    
    Args:
        path: Path to config.yaml
        
    Returns:
        AgentConfig instance
    """
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    config = AgentConfig()
    
    # Server config
    if 'server' in data:
        config.server = ServerConfig(**data['server'])
    
    # MLLP config
    if 'mllp' in data:
        config.mllp = MLLPConfig(**data['mllp'])
    
    # DICOM config
    if 'dicom' in data:
        config.dicom = DICOMConfig(**data['dicom'])
    
    # Logging config
    if 'logging' in data:
        config.logging = LoggingConfig(**data['logging'])
    
    # Agent identification
    if 'agent_id' in data:
        config.agent_id = data['agent_id']
    if 'agent_name' in data:
        config.agent_name = data['agent_name']
    
    return config


def save_config(config: AgentConfig, path: Path):
    """Save configuration to YAML file."""
    data = {
        'server': {
            'url': config.server.url,
            'api_key': config.server.api_key,
        },
        'mllp': {
            'enabled': config.mllp.enabled,
            'host': config.mllp.host,
            'port': config.mllp.port,
        },
        'dicom': {
            'enabled': config.dicom.enabled,
            'host': config.dicom.host,
            'port': config.dicom.port,
            'ae_title': config.dicom.ae_title,
        },
        'logging': {
            'level': config.logging.level,
            'file': config.logging.file,
        },
        'agent_name': config.agent_name,
    }
    
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

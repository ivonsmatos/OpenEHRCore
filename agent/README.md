# OpenEHRCore Agent

On-premise agent for connecting legacy healthcare devices to HealthStack.

## Supported Protocols

- **HL7 v2.x** via MLLP (Minimal Lower Layer Protocol)
- **DICOM** (C-STORE, C-ECHO) - Coming soon
- **ASTM** - Coming soon

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Hospital Network (On-Premise)                           │
│                                                          │
│  [Lab Analyzer] ──HL7/MLLP──┐                           │
│  [ECG Machine]  ──HL7/MLLP──┼──> 🤖 HealthStack Agent  │
│  [PACS/CT/MRI]  ──DICOM─────┘         │                 │
│                                        │                 │
└────────────────────────────────────────│─────────────────┘
                                         │ HTTPS/WebSocket
                                         ▼
┌─────────────────────────────────────────────────────────┐
│ Cloud / Data Center                                      │
│                                                          │
│  [HealthStack Server] ──> HAPI FHIR ──> PostgreSQL      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Requirements

- Python 3.10+
- Network access to OpenEHRCore server

### Quick Start

```bash
# 1. Navigate to agent directory
cd agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your settings

# 4. Run
python -m openehrcore_agent
```

### Configuration

```yaml
# config.yaml

server:
  url: https://your-openehrcore-server.com
  api_key: your-api-key

mllp:
  enabled: true
  host: 0.0.0.0
  port: 2575

dicom:
  enabled: false
  host: 0.0.0.0
  port: 4242
  ae_title: OPENEHRCORE

logging:
  level: INFO
  file: agent.log
```

## Features

### HL7/MLLP Listener

Receives HL7 v2.x messages via MLLP and forwards to OpenEHRCore:

- ADT (Admit/Discharge/Transfer)
- ORM (Orders)
- ORU (Results)
- SIU (Scheduling)

### WebSocket Connection

Maintains persistent secure connection to OpenEHRCore for:

- Real-time message forwarding
- Push notifications to devices
- Status monitoring

### Auto-Reconnect

Automatically reconnects if connection is lost.

### Audit Logging

All messages are logged locally and sent to OpenEHRCore AuditEvent.

## Running as Service

### Windows

```powershell
# Install as Windows Service
python install_service.py install

# Start service
python install_service.py start
```

### Linux (systemd)

```bash
# Copy service file
sudo cp openehrcore-agent.service /etc/systemd/system/

# Enable and start
sudo systemctl enable openehrcore-agent
sudo systemctl start openehrcore-agent
```

## Testing

```bash
# Send test HL7 message
python -m openehrcore_agent.test_mllp

# Check status
python -m openehrcore_agent.status
```

## License

MIT License - Same as HealthStack

"""
Bot Automation Engine - Serverless functions for healthcare workflows

Sprint 29: Bots/Automation

Features:
- Trigger-based execution (on resource changes)
- Cron job scheduling
- Custom FHIR operations
- Integration webhooks
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BotTriggerType(Enum):
    """Types of bot triggers."""
    RESOURCE_CREATE = 'resource-create'
    RESOURCE_UPDATE = 'resource-update'
    RESOURCE_DELETE = 'resource-delete'
    SCHEDULE = 'schedule'
    WEBHOOK = 'webhook'
    MANUAL = 'manual'


class BotStatus(Enum):
    """Bot execution status."""
    IDLE = 'idle'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    DISABLED = 'disabled'


class Bot:
    """
    Represents an automation bot.
    
    Bots are serverless functions that execute based on triggers.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        trigger_type: BotTriggerType,
        trigger_config: Dict,
        code: str,
        enabled: bool = True
    ):
        self.id = id
        self.name = name
        self.description = description
        self.trigger_type = trigger_type
        self.trigger_config = trigger_config
        self.code = code
        self.enabled = enabled
        self.status = BotStatus.IDLE
        self.last_run = None
        self.run_count = 0
        self.error_count = 0
        self.created_at = datetime.utcnow()


class BotExecutionContext:
    """Context passed to bot during execution."""
    
    def __init__(
        self,
        bot: Bot,
        trigger_data: Dict,
        fhir_service: Any = None,
        ai_service: Any = None
    ):
        self.bot = bot
        self.trigger_data = trigger_data
        self.fhir_service = fhir_service
        self.ai_service = ai_service
        self.logs: List[str] = []
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
    
    def log(self, message: str):
        """Add log message."""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
        logger.info(f"Bot {self.bot.id}: {message}")
    
    def create_resource(self, resource_type: str, data: Dict) -> Dict:
        """Create a FHIR resource."""
        if self.fhir_service:
            return self.fhir_service.create_resource(resource_type, data)
        raise RuntimeError("FHIR service not available")
    
    def search_resources(self, resource_type: str, params: Dict) -> List[Dict]:
        """Search FHIR resources."""
        if self.fhir_service:
            return self.fhir_service.search_resources(resource_type, params)
        raise RuntimeError("FHIR service not available")
    
    def update_resource(self, resource_type: str, resource_id: str, data: Dict) -> Dict:
        """Update a FHIR resource."""
        if self.fhir_service:
            return self.fhir_service.update_resource(resource_type, resource_id, data)
        raise RuntimeError("FHIR service not available")
    
    def send_notification(self, channel: str, message: str):
        """Send notification to a channel."""
        self.log(f"Sending notification to {channel}: {message[:50]}...")
        # TODO: Integrate with Mattermost
    
    def generate_ai_summary(self, patient_data: Dict) -> str:
        """Generate AI summary for patient."""
        if self.ai_service:
            result = self.ai_service.generate_patient_summary(patient_data)
            return result.get('summary', '')
        return "AI service not available"


class BotEngine:
    """
    Engine for managing and executing bots.
    
    Handles bot lifecycle, trigger matching, and execution.
    """
    
    def __init__(self):
        self.bots: Dict[str, Bot] = {}
        self.execution_history: List[Dict] = []
        self._load_default_bots()
    
    def _load_default_bots(self):
        """Load default/built-in bots."""
        # Bot 1: Welcome Patient
        self.register_bot(Bot(
            id='welcome-patient',
            name='Welcome Patient',
            description='Sends welcome message when new patient is registered',
            trigger_type=BotTriggerType.RESOURCE_CREATE,
            trigger_config={'resource_type': 'Patient'},
            code='''
def execute(ctx):
    patient = ctx.trigger_data.get('resource', {})
    name = patient.get('name', [{}])[0].get('given', [''])[0]
    ctx.log(f"New patient registered: {name}")
    ctx.send_notification('mattermost', f"🎉 Novo paciente cadastrado: {name}")
    return {"status": "welcomed", "patient": name}
'''
        ))
        
        # Bot 2: Critical Vital Alert
        self.register_bot(Bot(
            id='critical-vital-alert',
            name='Critical Vital Signs Alert',
            description='Alerts when vital signs are outside normal range',
            trigger_type=BotTriggerType.RESOURCE_CREATE,
            trigger_config={'resource_type': 'Observation', 'category': 'vital-signs'},
            code='''
def execute(ctx):
    obs = ctx.trigger_data.get('resource', {})
    code = obs.get('code', {}).get('coding', [{}])[0].get('code', '')
    value = obs.get('valueQuantity', {}).get('value', 0)
    
    # Check critical ranges
    alerts = []
    if code == '8867-4' and (value > 120 or value < 50):  # Heart rate
        alerts.append(f"⚠️ Frequência cardíaca crítica: {value} bpm")
    if code == '8480-6' and value > 180:  # Systolic BP
        alerts.append(f"🚨 Pressão sistólica muito alta: {value} mmHg")
    if code == '8310-5' and value > 39:  # Temperature
        alerts.append(f"🌡️ Febre alta: {value}°C")
    
    if alerts:
        ctx.send_notification('mattermost', '\\n'.join(alerts))
        ctx.log(f"Critical alert sent: {alerts}")
    
    return {"alerts": alerts}
'''
        ))
        
        # Bot 3: Daily Summary
        self.register_bot(Bot(
            id='daily-summary',
            name='Daily Clinical Summary',
            description='Generates daily summary of clinical activities',
            trigger_type=BotTriggerType.SCHEDULE,
            trigger_config={'cron': '0 18 * * *'},  # Daily at 6 PM
            code='''
def execute(ctx):
    # Get today's encounters
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    encounters = ctx.search_resources('Encounter', {
        'date': f'ge{today}',
        '_count': '100'
    })
    
    summary = f"📊 Resumo do dia {today}\\n"
    summary += f"Total de atendimentos: {len(encounters)}\\n"
    
    ctx.send_notification('mattermost', summary)
    ctx.log(f"Daily summary generated: {len(encounters)} encounters")
    
    return {"date": today, "encounters_count": len(encounters)}
'''
        ))
        
        # Bot 4: Lab Result Notifier
        self.register_bot(Bot(
            id='lab-result-notifier',
            name='Lab Result Notifier',
            description='Notifies when new lab results are available',
            trigger_type=BotTriggerType.RESOURCE_CREATE,
            trigger_config={'resource_type': 'DiagnosticReport'},
            code='''
def execute(ctx):
    report = ctx.trigger_data.get('resource', {})
    patient_ref = report.get('subject', {}).get('reference', '')
    status = report.get('status', 'final')
    
    if status == 'final':
        ctx.log(f"New lab result for {patient_ref}")
        ctx.send_notification('mattermost', f"🔬 Novo resultado de exame disponível para {patient_ref}")
    
    return {"patient": patient_ref, "status": status}
'''
        ))
    
    def register_bot(self, bot: Bot):
        """Register a new bot."""
        self.bots[bot.id] = bot
        logger.info(f"Registered bot: {bot.name} ({bot.id})")
    
    def unregister_bot(self, bot_id: str) -> bool:
        """Unregister a bot."""
        if bot_id in self.bots:
            del self.bots[bot_id]
            logger.info(f"Unregistered bot: {bot_id}")
            return True
        return False
    
    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """Get a bot by ID."""
        return self.bots.get(bot_id)
    
    def list_bots(self) -> List[Dict]:
        """List all registered bots."""
        return [
            {
                'id': bot.id,
                'name': bot.name,
                'description': bot.description,
                'trigger_type': bot.trigger_type.value,
                'enabled': bot.enabled,
                'status': bot.status.value,
                'last_run': bot.last_run.isoformat() if bot.last_run else None,
                'run_count': bot.run_count,
                'error_count': bot.error_count
            }
            for bot in self.bots.values()
        ]
    
    def execute_bot(
        self,
        bot_id: str,
        trigger_data: Dict,
        fhir_service: Any = None,
        ai_service: Any = None
    ) -> Dict[str, Any]:
        """
        Execute a bot with given trigger data.
        
        Args:
            bot_id: ID of bot to execute
            trigger_data: Data from trigger (resource, etc.)
            fhir_service: Optional FHIR service for data access
            ai_service: Optional AI service for intelligence
        
        Returns:
            Execution result
        """
        bot = self.get_bot(bot_id)
        if not bot:
            return {'success': False, 'error': f'Bot not found: {bot_id}'}
        
        if not bot.enabled:
            return {'success': False, 'error': f'Bot is disabled: {bot_id}'}
        
        # Create execution context
        ctx = BotExecutionContext(bot, trigger_data, fhir_service, ai_service)
        
        # Update bot status
        bot.status = BotStatus.RUNNING
        start_time = datetime.utcnow()
        
        try:
            # Execute bot code
            result = self._execute_code(bot.code, ctx)
            
            bot.status = BotStatus.COMPLETED
            bot.last_run = datetime.utcnow()
            bot.run_count += 1
            
            execution_record = {
                'bot_id': bot_id,
                'success': True,
                'result': result,
                'logs': ctx.logs,
                'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bot execution failed: {bot_id} - {e}")
            
            bot.status = BotStatus.FAILED
            bot.error_count += 1
            
            execution_record = {
                'bot_id': bot_id,
                'success': False,
                'error': str(e),
                'logs': ctx.logs,
                'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Store execution history
        self.execution_history.append(execution_record)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
        
        return execution_record
    
    def _execute_code(self, code: str, ctx: BotExecutionContext) -> Any:
        """Execute bot code in sandbox."""
        # Security: Use restricted globals
        safe_globals = {
            'ctx': ctx,
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'bool': bool,
                'print': lambda x: ctx.log(str(x)),
                'range': range,
                'enumerate': enumerate,
            }
        }
        
        # Compile and execute
        exec(code, safe_globals)
        
        # Call execute function if defined
        if 'execute' in safe_globals:
            return safe_globals['execute'](ctx)
        
        return None
    
    def trigger_bots(
        self,
        trigger_type: BotTriggerType,
        resource_type: str,
        trigger_data: Dict,
        fhir_service: Any = None,
        ai_service: Any = None
    ) -> List[Dict]:
        """
        Trigger all matching bots.
        
        Args:
            trigger_type: Type of trigger
            resource_type: Type of FHIR resource
            trigger_data: Data from trigger
            fhir_service: Optional FHIR service
            ai_service: Optional AI service
        
        Returns:
            List of execution results
        """
        results = []
        
        for bot in self.bots.values():
            if not bot.enabled:
                continue
            
            if bot.trigger_type != trigger_type:
                continue
            
            # Check resource type match
            config_type = bot.trigger_config.get('resource_type')
            if config_type and config_type != resource_type:
                continue
            
            # Execute bot
            result = self.execute_bot(
                bot.id,
                trigger_data,
                fhir_service,
                ai_service
            )
            results.append(result)
        
        return results
    
    def get_execution_history(self, bot_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get bot execution history."""
        history = self.execution_history
        
        if bot_id:
            history = [h for h in history if h.get('bot_id') == bot_id]
        
        return history[-limit:][::-1]  # Most recent first


# Singleton instance
_bot_engine = None


def get_bot_engine() -> BotEngine:
    """Get the bot engine singleton."""
    global _bot_engine
    if _bot_engine is None:
        _bot_engine = BotEngine()
    return _bot_engine

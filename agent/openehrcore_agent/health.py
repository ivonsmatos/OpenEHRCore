"""
Health monitoring for OpenEHRCore Agent.
"""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .__main__ import OpenEHRCoreAgent

logger = logging.getLogger('openehrcore_agent.health')


class HealthMonitor:
    """
    Monitors agent health and reports to server.
    """
    
    def __init__(self, agent: 'OpenEHRCoreAgent'):
        self.agent = agent
        self.messages_processed = 0
        self.errors = 0
        self.last_message_time = None
        self.start_time = datetime.now()
    
    async def start(self):
        """Start health monitoring loop."""
        while self.agent.running:
            await self._report_health()
            await asyncio.sleep(60)  # Report every minute
    
    async def _report_health(self):
        """Report health status to server."""
        status = {
            'type': 'agent_health',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'messages_processed': self.messages_processed,
            'errors': self.errors,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'status': self.agent.get_status()
        }
        
        try:
            if self.agent.ws_client and self.agent.ws_client.connected:
                await self.agent.ws_client._message_queue.put(status)
                logger.debug("Health status reported")
        except Exception as e:
            logger.warning(f"Failed to report health: {e}")
    
    def record_message(self, success: bool = True):
        """Record a processed message."""
        if success:
            self.messages_processed += 1
        else:
            self.errors += 1
        
        self.last_message_time = datetime.now()
    
    def get_stats(self) -> dict:
        """Get health statistics."""
        return {
            'messages_processed': self.messages_processed,
            'errors': self.errors,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'error_rate': self.errors / max(1, self.messages_processed + self.errors)
        }

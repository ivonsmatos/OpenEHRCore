"""
OpenEHRCore Agent - On-Premise Healthcare Device Bridge

Main entry point for the agent application.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from .config import load_config, AgentConfig
from .mllp_server import MLLPServer
from .websocket_client import WebSocketClient
from .health import HealthMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('openehrcore_agent')


class OpenEHRCoreAgent:
    """
    Main agent class that coordinates all components.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.running = False
        
        # Components
        self.ws_client = WebSocketClient(
            server_url=config.server.url,
            api_key=config.server.api_key,
            on_message=self._handle_push_message
        )
        
        self.mllp_server = MLLPServer(
            host=config.mllp.host,
            port=config.mllp.port,
            on_message=self._handle_hl7_message
        ) if config.mllp.enabled else None
        
        self.health_monitor = HealthMonitor(self)
    
    async def start(self):
        """Start all agent components."""
        logger.info("Starting OpenEHRCore Agent...")
        self.running = True
        
        tasks = []
        
        # Start WebSocket connection
        tasks.append(asyncio.create_task(self.ws_client.connect()))
        
        # Start MLLP server if enabled
        if self.mllp_server:
            tasks.append(asyncio.create_task(self.mllp_server.start()))
            logger.info(f"MLLP server listening on {self.config.mllp.host}:{self.config.mllp.port}")
        
        # Start health monitor
        tasks.append(asyncio.create_task(self.health_monitor.start()))
        
        logger.info("OpenEHRCore Agent started successfully")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Agent shutdown requested")
    
    async def stop(self):
        """Stop all agent components."""
        logger.info("Stopping OpenEHRCore Agent...")
        self.running = False
        
        if self.mllp_server:
            await self.mllp_server.stop()
        
        await self.ws_client.disconnect()
        
        logger.info("OpenEHRCore Agent stopped")
    
    async def _handle_hl7_message(self, message: str, source: str) -> str:
        """
        Handle incoming HL7 message from MLLP.
        
        Args:
            message: Raw HL7 message
            source: Source IP address
            
        Returns:
            HL7 acknowledgment message
        """
        logger.info(f"Received HL7 message from {source}")
        
        try:
            # Forward to OpenEHRCore via WebSocket
            response = await self.ws_client.send_hl7_message(message, source)
            
            # Return ACK
            return self._create_ack(message, "AA")  # Application Accept
            
        except Exception as e:
            logger.error(f"Error processing HL7 message: {e}")
            return self._create_ack(message, "AE")  # Application Error
    
    async def _handle_push_message(self, message: dict):
        """
        Handle push message from OpenEHRCore server.
        
        This allows the server to send messages to devices.
        """
        logger.info(f"Received push message: {message.get('type')}")
        
        msg_type = message.get('type')
        
        if msg_type == 'hl7_send':
            # Send HL7 message to a device
            destination = message.get('destination')
            hl7_message = message.get('message')
            # TODO: Implement outbound HL7 client
            pass
        
        elif msg_type == 'config_reload':
            # Reload configuration
            logger.info("Reloading configuration...")
            # TODO: Implement config reload
            pass
    
    def _create_ack(self, original_message: str, ack_code: str) -> str:
        """
        Create HL7 ACK message.
        
        Args:
            original_message: Original HL7 message
            ack_code: AA (accept), AE (error), AR (reject)
            
        Returns:
            HL7 ACK message
        """
        import datetime
        
        # Parse MSH from original
        segments = original_message.split('\r')
        msh = segments[0] if segments else ''
        msh_fields = msh.split('|')
        
        # Extract fields for ACK
        sending_app = msh_fields[2] if len(msh_fields) > 2 else ''
        sending_fac = msh_fields[3] if len(msh_fields) > 3 else ''
        receiving_app = msh_fields[4] if len(msh_fields) > 4 else ''
        receiving_fac = msh_fields[5] if len(msh_fields) > 5 else ''
        msg_control_id = msh_fields[9] if len(msh_fields) > 9 else ''
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        ack = (
            f"MSH|^~\\&|{receiving_app}|{receiving_fac}|{sending_app}|{sending_fac}|"
            f"{timestamp}||ACK|{timestamp}|P|2.5.1\r"
            f"MSA|{ack_code}|{msg_control_id}\r"
        )
        
        return ack
    
    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "running": self.running,
            "websocket_connected": self.ws_client.connected if self.ws_client else False,
            "mllp_active": self.mllp_server.active if self.mllp_server else False,
            "messages_processed": self.health_monitor.messages_processed
        }


async def main():
    """Main entry point."""
    # Load configuration
    config_path = Path(__file__).parent.parent / 'config.yaml'
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Copy config.example.yaml to config.yaml and configure it")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Create and start agent
    agent = OpenEHRCoreAgent(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(agent.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run agent
    await agent.start()


if __name__ == '__main__':
    asyncio.run(main())

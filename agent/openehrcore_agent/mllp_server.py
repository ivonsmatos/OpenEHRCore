"""
MLLP (Minimal Lower Layer Protocol) Server for HL7 v2.x messages.

MLLP framing:
- Start block: 0x0B (vertical tab)
- End block: 0x1C 0x0D (file separator + carriage return)
"""

import asyncio
import logging
from typing import Callable, Optional, Awaitable

logger = logging.getLogger('openehrcore_agent.mllp')

# MLLP framing characters
MLLP_START_BLOCK = b'\x0b'  # VT (vertical tab)
MLLP_END_BLOCK = b'\x1c\x0d'  # FS + CR


class MLLPProtocol(asyncio.Protocol):
    """
    Asyncio protocol for MLLP connections.
    """
    
    def __init__(
        self,
        on_message: Callable[[str, str], Awaitable[str]],
        timeout: int = 30
    ):
        self.on_message = on_message
        self.timeout = timeout
        self.transport = None
        self.buffer = b''
        self.peer = None
    
    def connection_made(self, transport):
        """Called when connection is established."""
        self.transport = transport
        self.peer = transport.get_extra_info('peername')
        logger.info(f"MLLP connection from {self.peer}")
    
    def data_received(self, data: bytes):
        """Called when data is received."""
        self.buffer += data
        
        # Check for complete MLLP message
        while MLLP_START_BLOCK in self.buffer and MLLP_END_BLOCK in self.buffer:
            start_idx = self.buffer.find(MLLP_START_BLOCK)
            end_idx = self.buffer.find(MLLP_END_BLOCK)
            
            if start_idx < end_idx:
                # Extract message (without framing)
                message = self.buffer[start_idx + 1:end_idx].decode('utf-8', errors='replace')
                
                # Remove processed data from buffer
                self.buffer = self.buffer[end_idx + 2:]
                
                # Process message
                asyncio.create_task(self._process_message(message))
            else:
                # Invalid framing, discard up to start
                self.buffer = self.buffer[start_idx:]
                break
    
    async def _process_message(self, message: str):
        """Process received HL7 message."""
        try:
            logger.debug(f"Processing HL7 message from {self.peer}")
            
            # Get source IP
            source = self.peer[0] if self.peer else 'unknown'
            
            # Call handler
            response = await self.on_message(message, source)
            
            # Send response wrapped in MLLP framing
            if response:
                response_bytes = MLLP_START_BLOCK + response.encode('utf-8') + MLLP_END_BLOCK
                self.transport.write(response_bytes)
                logger.debug(f"Sent ACK to {self.peer}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def connection_lost(self, exc):
        """Called when connection is lost."""
        if exc:
            logger.warning(f"MLLP connection lost from {self.peer}: {exc}")
        else:
            logger.info(f"MLLP connection closed from {self.peer}")


class MLLPServer:
    """
    MLLP server for receiving HL7 v2.x messages.
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 2575,
        on_message: Callable[[str, str], Awaitable[str]] = None,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.on_message = on_message or self._default_handler
        self.timeout = timeout
        self.server = None
        self.active = False
        self._connections = set()
    
    async def start(self):
        """Start the MLLP server."""
        loop = asyncio.get_event_loop()
        
        def protocol_factory():
            protocol = MLLPProtocol(self.on_message, self.timeout)
            self._connections.add(protocol)
            return protocol
        
        self.server = await loop.create_server(
            protocol_factory,
            self.host,
            self.port
        )
        
        self.active = True
        logger.info(f"MLLP server started on {self.host}:{self.port}")
        
        # Keep server running
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the MLLP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.active = False
            logger.info("MLLP server stopped")
    
    async def _default_handler(self, message: str, source: str) -> str:
        """Default message handler - just logs and ACKs."""
        logger.info(f"Received HL7 from {source}: {len(message)} bytes")
        
        # Return simple ACK
        return "MSH|^~\\&|AGENT|OPENEHRCORE|||20241213||ACK|1|P|2.5.1\rMSA|AA|1\r"
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len([c for c in self._connections if c.transport and not c.transport.is_closing()])


# Utility functions

def parse_hl7_message(message: str) -> dict:
    """
    Parse HL7 message into segments.
    
    Returns:
        Dict with segment name as key and list of fields as value
    """
    segments = {}
    
    for line in message.split('\r'):
        if not line:
            continue
        
        fields = line.split('|')
        segment_name = fields[0]
        
        if segment_name not in segments:
            segments[segment_name] = []
        
        segments[segment_name].append(fields)
    
    return segments


def get_message_type(message: str) -> str:
    """Get HL7 message type (e.g., 'ADT^A01')."""
    segments = parse_hl7_message(message)
    
    if 'MSH' in segments and segments['MSH']:
        msh = segments['MSH'][0]
        if len(msh) > 9:
            return msh[9]
    
    return 'UNKNOWN'


def get_patient_id(message: str) -> Optional[str]:
    """Extract patient ID from HL7 message."""
    segments = parse_hl7_message(message)
    
    if 'PID' in segments and segments['PID']:
        pid = segments['PID'][0]
        if len(pid) > 3:
            return pid[3].split('^')[0] if pid[3] else None
    
    return None

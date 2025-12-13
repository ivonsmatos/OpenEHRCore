"""
WebSocket client for secure connection to OpenEHRCore server.
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Awaitable
from datetime import datetime

logger = logging.getLogger('openehrcore_agent.websocket')

# Try to import websockets, fall back gracefully
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets package not installed, using HTTP fallback")


class WebSocketClient:
    """
    WebSocket client for real-time communication with OpenEHRCore.
    
    Features:
    - Auto-reconnect on disconnect
    - Heartbeat/ping-pong
    - Message queue for offline messages
    """
    
    def __init__(
        self,
        server_url: str,
        api_key: str,
        on_message: Callable[[dict], Awaitable[None]] = None,
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 0  # 0 = infinite
    ):
        self.server_url = server_url
        self.api_key = api_key
        self.on_message = on_message
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # State
        self.websocket = None
        self.connected = False
        self._reconnect_count = 0
        self._message_queue = asyncio.Queue()
        self._running = False
    
    async def connect(self):
        """
        Connect to WebSocket server and maintain connection.
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket not available, using HTTP polling")
            await self._http_polling_loop()
            return
        
        self._running = True
        
        while self._running:
            try:
                await self._connect_websocket()
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
            
            if not self._running:
                break
            
            # Reconnect logic
            self._reconnect_count += 1
            
            if self.max_reconnect_attempts > 0 and self._reconnect_count >= self.max_reconnect_attempts:
                logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached")
                break
            
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)
    
    async def _connect_websocket(self):
        """Establish WebSocket connection."""
        ws_url = self._get_websocket_url()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        logger.info(f"Connecting to {ws_url}...")
        
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            self.websocket = ws
            self.connected = True
            self._reconnect_count = 0
            
            logger.info("WebSocket connected")
            
            # Start message sender
            sender_task = asyncio.create_task(self._message_sender())
            
            try:
                # Listen for messages
                async for message in ws:
                    await self._handle_incoming_message(message)
            finally:
                sender_task.cancel()
                self.connected = False
                self.websocket = None
    
    async def _message_sender(self):
        """Send queued messages."""
        while self.connected:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=30.0
                )
                
                if self.websocket:
                    await self.websocket.send(json.dumps(message))
                    logger.debug(f"Sent message: {message.get('type')}")
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                if self.websocket:
                    await self.websocket.ping()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    async def _handle_incoming_message(self, raw_message: str):
        """Handle incoming WebSocket message."""
        try:
            message = json.loads(raw_message)
            
            msg_type = message.get('type')
            logger.debug(f"Received message: {msg_type}")
            
            if msg_type == 'ping':
                # Respond to ping
                await self._message_queue.put({'type': 'pong'})
            
            elif self.on_message:
                await self.on_message(message)
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message: {raw_message[:100]}")
    
    async def send_hl7_message(self, hl7_message: str, source: str) -> dict:
        """
        Send HL7 message to OpenEHRCore.
        
        Args:
            hl7_message: Raw HL7 message
            source: Source IP/identifier
            
        Returns:
            Response from server
        """
        message = {
            'type': 'hl7_message',
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'payload': hl7_message
        }
        
        if self.connected and self.websocket:
            # Send via WebSocket
            await self._message_queue.put(message)
            return {'status': 'sent', 'method': 'websocket'}
        else:
            # Fallback to HTTP
            return await self._send_http(message)
    
    async def _send_http(self, message: dict) -> dict:
        """Send message via HTTP (fallback)."""
        import aiohttp
        
        url = f"{self.server_url}/api/v1/hl7/receive"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=message, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.error(f"HTTP error: {resp.status}")
                        return {'status': 'error', 'code': resp.status}
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _http_polling_loop(self):
        """HTTP polling fallback when WebSocket not available."""
        import aiohttp
        
        self._running = True
        
        while self._running:
            try:
                # Check for pending messages from server
                url = f"{self.server_url}/api/v1/agent/messages"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            messages = await resp.json()
                            for msg in messages.get('messages', []):
                                if self.on_message:
                                    await self.on_message(msg)
                
            except Exception as e:
                logger.debug(f"Polling error: {e}")
            
            await asyncio.sleep(5)
    
    async def disconnect(self):
        """Disconnect from server."""
        self._running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def _get_websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL."""
        if self.server_url.startswith('https://'):
            return self.server_url.replace('https://', 'wss://') + '/ws/agent/'
        else:
            return self.server_url.replace('http://', 'ws://') + '/ws/agent/'

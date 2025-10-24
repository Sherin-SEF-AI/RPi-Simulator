"""
Cloud Platform Connectors for IoT Integration
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import threading
import queue


@dataclass
class IoTMessage:
    """IoT message structure"""
    device_id: str
    timestamp: float
    data: Dict[str, Any]
    message_type: str = "telemetry"
    properties: Dict[str, str] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class CloudConnector(ABC):
    """Base class for cloud platform connectors"""
    
    def __init__(self, device_id: str, connection_string: str):
        self.device_id = device_id
        self.connection_string = connection_string
        self.connected = False
        self.message_queue = queue.Queue()
        self.callbacks: Dict[str, List[Callable]] = {}
        
    @abstractmethod
    def connect(self) -> bool:
        """Connect to cloud platform"""
        pass
        
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from cloud platform"""
        pass
        
    @abstractmethod
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """Send telemetry data"""
        pass
        
    @abstractmethod
    def send_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """Send event data"""
        pass
        
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add callback for cloud events"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        
    def _trigger_callback(self, event_type: str, data: Any) -> None:
        """Trigger callbacks for event type"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Callback error: {e}")


class AzureIoTConnector(CloudConnector):
    """Microsoft Azure IoT Hub connector"""
    
    def __init__(self, device_id: str, connection_string: str):
        super().__init__(device_id, connection_string)
        self.hub_name = self._extract_hub_name(connection_string)
        self.device_key = self._extract_device_key(connection_string)
        
        # Simulation state
        self.telemetry_count = 0
        self.last_heartbeat = 0.0
        
    def _extract_hub_name(self, conn_str: str) -> str:
        """Extract hub name from connection string"""
        # Parse Azure IoT connection string
        parts = dict(part.split('=', 1) for part in conn_str.split(';') if '=' in part)
        hostname = parts.get('HostName', 'demo-hub.azure-devices.net')
        return hostname.split('.')[0]
        
    def _extract_device_key(self, conn_str: str) -> str:
        """Extract device key from connection string"""
        parts = dict(part.split('=', 1) for part in conn_str.split(';') if '=' in part)
        return parts.get('SharedAccessKey', 'demo-key')
        
    def connect(self) -> bool:
        """Connect to Azure IoT Hub"""
        try:
            # Simulate connection process
            print(f"🔗 Connecting to Azure IoT Hub: {self.hub_name}")
            print(f"📱 Device ID: {self.device_id}")
            
            # Simulate authentication
            time.sleep(0.5)
            
            self.connected = True
            self.last_heartbeat = time.time()
            
            print("✅ Connected to Azure IoT Hub")
            self._trigger_callback("connected", {"hub": self.hub_name})
            
            # Start heartbeat thread
            self._start_heartbeat()
            
            return True
            
        except Exception as e:
            print(f"❌ Azure IoT connection failed: {e}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from Azure IoT Hub"""
        self.connected = False
        print("🔌 Disconnected from Azure IoT Hub")
        self._trigger_callback("disconnected", {})
        
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """Send telemetry to Azure IoT Hub"""
        if not self.connected:
            return False
            
        try:
            message = IoTMessage(
                device_id=self.device_id,
                timestamp=time.time(),
                data=data,
                message_type="telemetry"
            )
            
            # Simulate sending to Azure
            self.telemetry_count += 1
            
            print(f"📊 Azure Telemetry #{self.telemetry_count}: {json.dumps(data, indent=2)}")
            
            self._trigger_callback("telemetry_sent", {
                "message": message,
                "count": self.telemetry_count
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Azure telemetry send failed: {e}")
            return False
            
    def send_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """Send event to Azure IoT Hub"""
        if not self.connected:
            return False
            
        try:
            message = IoTMessage(
                device_id=self.device_id,
                timestamp=time.time(),
                data=data,
                message_type="event",
                properties={"eventType": event_name}
            )
            
            print(f"🚨 Azure Event '{event_name}': {json.dumps(data, indent=2)}")
            
            self._trigger_callback("event_sent", {
                "event_name": event_name,
                "message": message
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Azure event send failed: {e}")
            return False
            
    def _start_heartbeat(self) -> None:
        """Start heartbeat thread"""
        def heartbeat_loop():
            while self.connected:
                current_time = time.time()
                if current_time - self.last_heartbeat > 30:  # 30 second heartbeat
                    self.send_telemetry({
                        "heartbeat": True,
                        "uptime": current_time - self.last_heartbeat
                    })
                    self.last_heartbeat = current_time
                time.sleep(5)
                
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
        
    def receive_cloud_to_device_message(self) -> Optional[Dict[str, Any]]:
        """Simulate receiving cloud-to-device message"""
        # Simulate occasional cloud messages
        import random
        if random.random() < 0.1:  # 10% chance
            return {
                "messageId": str(uuid.uuid4()),
                "command": "update_config",
                "data": {
                    "sample_rate": 5000,
                    "enable_debug": True
                }
            }
        return None


class AWSIoTConnector(CloudConnector):
    """Amazon AWS IoT Core connector"""
    
    def __init__(self, device_id: str, endpoint: str, cert_path: str = None):
        super().__init__(device_id, endpoint)
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.thing_name = device_id
        
        # AWS IoT topics
        self.telemetry_topic = f"device/{self.device_id}/telemetry"
        self.event_topic = f"device/{self.device_id}/events"
        self.shadow_topic = f"$aws/things/{self.thing_name}/shadow"
        
    def connect(self) -> bool:
        """Connect to AWS IoT Core"""
        try:
            print(f"🔗 Connecting to AWS IoT Core: {self.endpoint}")
            print(f"📱 Thing Name: {self.thing_name}")
            
            # Simulate certificate validation
            if self.cert_path:
                print(f"🔐 Using certificate: {self.cert_path}")
            
            time.sleep(0.5)
            
            self.connected = True
            print("✅ Connected to AWS IoT Core")
            
            self._trigger_callback("connected", {"endpoint": self.endpoint})
            return True
            
        except Exception as e:
            print(f"❌ AWS IoT connection failed: {e}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from AWS IoT Core"""
        self.connected = False
        print("🔌 Disconnected from AWS IoT Core")
        
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """Send telemetry to AWS IoT Core"""
        if not self.connected:
            return False
            
        try:
            payload = {
                "timestamp": int(time.time() * 1000),
                "deviceId": self.device_id,
                "data": data
            }
            
            print(f"📊 AWS IoT Telemetry -> {self.telemetry_topic}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            self._trigger_callback("telemetry_sent", {
                "topic": self.telemetry_topic,
                "payload": payload
            })
            
            return True
            
        except Exception as e:
            print(f"❌ AWS IoT telemetry send failed: {e}")
            return False
            
    def send_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """Send event to AWS IoT Core"""
        if not self.connected:
            return False
            
        try:
            payload = {
                "timestamp": int(time.time() * 1000),
                "deviceId": self.device_id,
                "eventType": event_name,
                "data": data
            }
            
            print(f"🚨 AWS IoT Event -> {self.event_topic}")
            print(f"   Event: {event_name}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ AWS IoT event send failed: {e}")
            return False
            
    def update_device_shadow(self, desired_state: Dict[str, Any]) -> bool:
        """Update AWS IoT device shadow"""
        if not self.connected:
            return False
            
        try:
            shadow_update = {
                "state": {
                    "desired": desired_state
                },
                "metadata": {
                    "desired": {
                        key: {"timestamp": int(time.time())}
                        for key in desired_state.keys()
                    }
                }
            }
            
            print(f"👤 AWS IoT Shadow Update -> {self.shadow_topic}/update")
            print(f"   Desired State: {json.dumps(desired_state, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ AWS IoT shadow update failed: {e}")
            return False


class GoogleCloudIoTConnector(CloudConnector):
    """Google Cloud IoT Core connector"""
    
    def __init__(self, device_id: str, project_id: str, region: str, registry_id: str):
        super().__init__(device_id, f"{project_id}/{region}/{registry_id}")
        self.project_id = project_id
        self.region = region
        self.registry_id = registry_id
        
        # Google Cloud IoT topics
        self.telemetry_topic = f"projects/{project_id}/topics/device-telemetry"
        self.event_topic = f"projects/{project_id}/topics/device-events"
        
    def connect(self) -> bool:
        """Connect to Google Cloud IoT Core"""
        try:
            print(f"🔗 Connecting to Google Cloud IoT Core")
            print(f"📱 Project: {self.project_id}")
            print(f"🌍 Region: {self.region}")
            print(f"📋 Registry: {self.registry_id}")
            print(f"🔧 Device: {self.device_id}")
            
            time.sleep(0.5)
            
            self.connected = True
            print("✅ Connected to Google Cloud IoT Core")
            
            return True
            
        except Exception as e:
            print(f"❌ Google Cloud IoT connection failed: {e}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from Google Cloud IoT Core"""
        self.connected = False
        print("🔌 Disconnected from Google Cloud IoT Core")
        
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """Send telemetry to Google Cloud IoT Core"""
        if not self.connected:
            return False
            
        try:
            payload = {
                "deviceId": self.device_id,
                "timestamp": time.time(),
                "telemetry": data
            }
            
            print(f"📊 Google Cloud IoT Telemetry -> {self.telemetry_topic}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Google Cloud IoT telemetry send failed: {e}")
            return False
            
    def send_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        """Send event to Google Cloud IoT Core"""
        if not self.connected:
            return False
            
        try:
            payload = {
                "deviceId": self.device_id,
                "timestamp": time.time(),
                "eventType": event_name,
                "eventData": data
            }
            
            print(f"🚨 Google Cloud IoT Event -> {self.event_topic}")
            print(f"   Event: {event_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Google Cloud IoT event send failed: {e}")
            return False


class IoTCloudManager:
    """Manage multiple cloud connections"""
    
    def __init__(self):
        self.connectors: Dict[str, CloudConnector] = {}
        self.active_connector: Optional[str] = None
        
    def add_connector(self, name: str, connector: CloudConnector) -> None:
        """Add a cloud connector"""
        self.connectors[name] = connector
        
    def set_active_connector(self, name: str) -> bool:
        """Set active cloud connector"""
        if name in self.connectors:
            self.active_connector = name
            return True
        return False
        
    def connect_all(self) -> Dict[str, bool]:
        """Connect to all configured cloud platforms"""
        results = {}
        for name, connector in self.connectors.items():
            results[name] = connector.connect()
        return results
        
    def send_to_all(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Send telemetry to all connected platforms"""
        results = {}
        for name, connector in self.connectors.items():
            if connector.connected:
                results[name] = connector.send_telemetry(data)
            else:
                results[name] = False
        return results
        
    def send_to_active(self, data: Dict[str, Any]) -> bool:
        """Send telemetry to active connector"""
        if self.active_connector and self.active_connector in self.connectors:
            connector = self.connectors[self.active_connector]
            if connector.connected:
                return connector.send_telemetry(data)
        return False
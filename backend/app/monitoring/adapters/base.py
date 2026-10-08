"""
Base Network Device Adapter
Abstract interface for all device adapters
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class NetworkDeviceAdapter(ABC):
    """
    Abstract base class for network device adapters.
    All vendor-specific adapters must implement this interface.
    """
    
    def __init__(self, device_id: int, management_ip: str, credentials: Dict[str, Any]):
        self.device_id = device_id
        self.management_ip = management_ip
        self.credentials = credentials
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connectivity to device.
        Returns: {success: bool, latency_ms: float, message: str, error_code: str}
        """
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """
        Get device system information.
        Returns: {hostname, vendor, model, serial, firmware, uptime, cpu, memory, temperature}
        """
        pass
    
    @abstractmethod
    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get list of interfaces.
        Returns: [{if_index, name, description, status, admin_status, speed, duplex, mtu}]
        """
        pass
    
    @abstractmethod
    async def get_interface_statistics(self) -> List[Dict[str, Any]]:
        """
        Get interface traffic statistics.
        Returns: [{if_index, rx_bytes, tx_bytes, rx_errors, tx_errors, rx_discards, tx_discards}]
        """
        pass
    
    async def close(self):
        """Cleanup resources"""
        pass

"""
Adapter Registry
Selects appropriate adapter based on device vendor/type
"""
from typing import Dict, Any, Optional
from .base import NetworkDeviceAdapter
from .snmp import GenericSNMPAdapter
from .aruba_cx import ArubaCXAdapter


class AdapterRegistry:
    """
    Registry for network device adapters.
    Selects the appropriate adapter based on device vendor and monitoring method.
    """
    
    @staticmethod
    def get_adapter(
        device_id: int,
        management_ip: str,
        vendor: str,
        device_type: str,
        monitoring_method: str,
        credentials: Dict[str, Any]
    ) -> NetworkDeviceAdapter:
        """
        Get appropriate adapter for device.
        
        Priority:
        1. If vendor is Aruba and monitoring_method is REST_API -> ArubaCXAdapter
        2. If monitoring_method is SNMP -> GenericSNMPAdapter
        3. Default -> GenericSNMPAdapter
        """
        
        # Aruba CX with REST API
        if vendor.lower() == 'aruba' and monitoring_method == 'rest_api':
            if credentials.get('api_enabled') and credentials.get('username') and credentials.get('password'):
                return ArubaCXAdapter(device_id, management_ip, credentials)
        
        # Default to SNMP for all other cases
        if monitoring_method in ['snmp', 'multi', 'none', '']:
            return GenericSNMPAdapter(device_id, management_ip, credentials)

        # No adapter implemented for this method (e.g. zabbix, ssh).
        # Fail explicitly instead of silently falling back to SNMP —
        # a silent fallback would poll devices via a protocol the
        # operator never configured them for.
        raise ValueError(f"No adapter available for monitoring method '{monitoring_method}'")

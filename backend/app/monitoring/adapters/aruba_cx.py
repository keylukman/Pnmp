"""
Aruba AOS-CX REST API Adapter
"""
import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from .base import NetworkDeviceAdapter


class ArubaCXAdapter(NetworkDeviceAdapter):
    """
    Aruba AOS-CX REST API adapter.
    Uses HTTPS REST API for monitoring and configuration.
    """
    
    def __init__(self, device_id: int, management_ip: str, credentials: Dict[str, Any]):
        super().__init__(device_id, management_ip, credentials)
        self.username = credentials.get('username', 'admin')
        self.password = credentials.get('password', '')
        self.timeout = credentials.get('timeout', 10)
        self.base_url = f"https://{management_ip}/rest/v1"
        self._client = None
        self._session_cookie = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                verify=False,  # Self-signed certs
                timeout=self.timeout
            )
        return self._client
    
    async def _authenticate(self) -> bool:
        """Authenticate with Aruba CX API"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/login",
                json={
                    'username': self.username,
                    'password': self.password
                }
            )
            
            if response.status_code == 200:
                self._session_cookie = response.cookies.get('session_id')
                return True
            return False
        except Exception as e:
            print(f"Aruba CX authentication failed: {e}")
            return False
    
    async def _api_get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make authenticated GET request"""
        try:
            if not self._session_cookie:
                if not await self._authenticate():
                    return None
            
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}{endpoint}",
                cookies={'session_id': self._session_cookie}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Re-authenticate
                if await self._authenticate():
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        cookies={'session_id': self._session_cookie}
                    )
                    if response.status_code == 200:
                        return response.json()
            return None
        except Exception as e:
            print(f"Aruba CX API error: {e}")
            return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Aruba CX API connectivity"""
        start_time = time.time()
        try:
            # Try to get system status
            result = await self._api_get("/system/status")
            latency_ms = (time.time() - start_time) * 1000
            
            if result:
                return {
                    'success': True,
                    'latency_ms': round(latency_ms, 2),
                    'message': f"Aruba CX API connection successful to {self.management_ip}",
                    'hostname': result.get('hostname', 'Unknown')
                }
            else:
                return {
                    'success': False,
                    'latency_ms': round(latency_ms, 2),
                    'message': "Aruba CX API authentication failed",
                    'error_code': 'AUTH_FAILED'
                }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                'success': False,
                'latency_ms': round(latency_ms, 2),
                'message': f"Aruba CX connection failed: {str(e)}",
                'error_code': 'CONNECTION_ERROR'
            }
    
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get device system information via Aruba CX API"""
        try:
            # Get system status
            status = await self._api_get("/system/status")
            if not status:
                return None
            
            # Get resource utilization
            resources = await self._api_get("/system/resource_utilization")
            
            # Parse uptime
            uptime_str = status.get('other_info', {}).get('uptime', '0')
            # Parse uptime string like "1 day, 2:30:45"
            uptime_seconds = 0
            try:
                parts = uptime_str.split(',')
                if 'day' in parts[0]:
                    days = int(parts[0].split()[0])
                    uptime_seconds += days * 86400
                if len(parts) > 1:
                    time_parts = parts[1].strip().split(':')
                    uptime_seconds += int(time_parts[0]) * 3600
                    uptime_seconds += int(time_parts[1]) * 60
                    uptime_seconds += int(time_parts[2])
            except:
                pass
            
            return {
                'hostname': status.get('hostname', 'Unknown'),
                'vendor': 'Aruba',
                'model': status.get('platform_name', 'Unknown'),
                'serial': status.get('serial_number', 'Unknown'),
                'firmware': status.get('firmware_version', 'Unknown'),
                'uptime_seconds': uptime_seconds,
                'cpu': resources.get('cpu', {}).get('cpu_utilization', 0) if resources else None,
                'memory': resources.get('memory', {}).get('memory_utilization', 0) if resources else None,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting Aruba CX system info: {e}")
            return None
    
    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get list of interfaces via Aruba CX API"""
        try:
            result = await self._api_get("/system/interfaces")
            if not result:
                return []
            
            interfaces = []
            for iface_name, iface_data in result.items():
                # Parse interface name (e.g., "1/1/1" or "lag1")
                interfaces.append({
                    'name': iface_name,
                    'description': iface_data.get('description', ''),
                    'alias': iface_data.get('user_config', {}).get('description', ''),
                    'admin_status': 'up' if iface_data.get('user_config', {}).get('admin_state', 'up') == 'up' else 'down',
                    'status': 'up' if iface_data.get('admin_state', 'up') == 'up' else 'down',
                    'speed_bps': iface_data.get('interface_statistics', {}).get('cur_rate', {}).get('speed', 0) * 1_000_000,
                    'mtu': iface_data.get('user_config', {}).get('mtu', None),
                    'duplex': 'full'  # Aruba CX is always full duplex
                })
            
            return interfaces
        except Exception as e:
            print(f"Error getting Aruba CX interfaces: {e}")
            return []
    
    async def get_interface_statistics(self) -> List[Dict[str, Any]]:
        """Get interface traffic statistics via Aruba CX API"""
        try:
            result = await self._api_get("/system/interfaces")
            if not result:
                return []
            
            stats = []
            for iface_name, iface_data in result.items():
                iface_stats = iface_data.get('interface_statistics', {})
                
                stats.append({
                    'name': iface_name,
                    'rx_bytes': iface_stats.get('in_octets', 0),
                    'tx_bytes': iface_stats.get('out_octets', 0),
                    'rx_errors': iface_stats.get('in_errors', 0),
                    'tx_errors': iface_stats.get('out_errors', 0),
                    'rx_discards': iface_stats.get('in_discards', 0),
                    'tx_discards': iface_stats.get('out_discards', 0),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return stats
        except Exception as e:
            print(f"Error getting Aruba CX interface statistics: {e}")
            return []
    
    async def close(self):
        """Cleanup HTTP client and logout"""
        if self._client and self._session_cookie:
            try:
                await self._client.post(
                    f"{self.base_url}/logout",
                    cookies={'session_id': self._session_cookie}
                )
            except:
                pass
        if self._client:
            await self._client.aclose()
            self._client = None
        self._session_cookie = None

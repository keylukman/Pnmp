"""
Generic SNMP Adapter
Supports SNMP v2c and v3
"""
import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import NetworkDeviceAdapter

# SNMP OIDs
OIDS = {
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'ifNumber': '1.3.6.1.2.1.2.1.0',
    'ifIndex': '1.3.6.1.2.1.2.2.1.1',
    'ifDescr': '1.3.6.1.2.1.2.2.1.2',
    'ifType': '1.3.6.1.2.1.2.2.1.3',
    'ifMtu': '1.3.6.1.2.1.2.2.1.4',
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
    'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
    'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
    'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
    'ifAlias': '1.3.6.1.2.1.31.1.1.1.18',
    'ifName': '1.3.6.1.2.1.31.1.1.1.1',
    'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',
    'ifHCOutOctets': '1.3.6.1.2.1.31.1.1.1.10',
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
    'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',
    'ifInDiscards': '1.3.6.1.2.1.2.2.1.13',
    'ifOutDiscards': '1.3.6.1.2.1.2.2.1.19',
    'ifHighSpeed': '1.3.6.1.2.1.31.1.1.1.15',
}


class GenericSNMPAdapter(NetworkDeviceAdapter):
    """
    Generic SNMP adapter for network devices.
    Supports SNMP v2c and v3.
    """
    
    def __init__(self, device_id: int, management_ip: str, credentials: Dict[str, Any]):
        super().__init__(device_id, management_ip, credentials)
        self.snmp_version = credentials.get('snmp_version', 'v2c')
        self.timeout = credentials.get('timeout', 5)
        self.retries = credentials.get('retries', 2)
        self._snmp_engine = None
    
    async def _get_snmp_engine(self):
        """Lazy load SNMP engine"""
        if self._snmp_engine is None:
            from pysnmp.hlapi.v3asyncio import SnmpEngine
            self._snmp_engine = SnmpEngine()
        return self._snmp_engine
    
    async def _snmp_get(self, oids: List[str]) -> Dict[str, Any]:
        """Perform SNMP GET operation"""
        from pysnmp.hlapi.v3asyncio import (
            get_cmd, CommunityData, UsmUserData,
            UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        )
        
        snmp_engine = await self._get_snmp_engine()
        
        # Build authentication
        if self.snmp_version == 'v3':
            auth_data = UsmUserData(
                self.credentials.get('snmp_username', ''),
                self.credentials.get('snmp_auth_password', ''),
                self.credentials.get('snmp_privacy_password', ''),
                authProtocol=getattr(
                    __import__('pysnmp.hlapi.v3asyncio', fromlist=['usm' + self.credentials.get('snmp_auth_protocol', 'SHA').upper()]),
                    'usm' + self.credentials.get('snmp_auth_protocol', 'SHA').upper() + 'Protocol'
                ) if self.credentials.get('snmp_auth_password') else None,
                privProtocol=getattr(
                    __import__('pysnmp.hlapi.v3asyncio', fromlist=['usm' + self.credentials.get('snmp_privacy_protocol', 'AES').upper() + 'Protocol']),
                    'usm' + self.credentials.get('snmp_privacy_protocol', 'AES').upper() + 'Protocol'
                ) if self.credentials.get('snmp_privacy_password') else None
            )
        else:
            auth_data = CommunityData(self.credentials.get('snmp_community', 'public'))
        
        # Build transport
        transport = await UdpTransportTarget.create(
            (self.management_ip, 161),
            timeout=self.timeout,
            retries=self.retries
        )
        
        # Build object types
        object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]
        
        # Execute GET
        error_indication, error_status, error_index, var_binds = await get_cmd(
            snmp_engine,
            auth_data,
            transport,
            ContextData(),
            *object_types
        )
        
        if error_indication:
            raise Exception(f"SNMP error: {error_indication}")
        elif error_status:
            raise Exception(f"SNMP error: {error_status}")
        
        # Parse results
        result = {}
        for var_bind in var_binds:
            oid, val = var_bind
            oid_str = str(oid)
            result[oid_str] = val.prettyPrint()
        
        return result
    
    async def _snmp_walk(self, oid: str) -> List[Dict[str, Any]]:
        """Perform SNMP WALK operation"""
        from pysnmp.hlapi.v3asyncio import (
            next_cmd, CommunityData, UsmUserData,
            UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        )
        
        snmp_engine = await self._get_snmp_engine()
        
        # Build authentication
        if self.snmp_version == 'v3':
            auth_data = UsmUserData(
                self.credentials.get('snmp_username', ''),
                self.credentials.get('snmp_auth_password', ''),
                self.credentials.get('snmp_privacy_password', '')
            )
        else:
            auth_data = CommunityData(self.credentials.get('snmp_community', 'public'))
        
        # Build transport
        transport = await UdpTransportTarget.create(
            (self.management_ip, 161),
            timeout=self.timeout,
            retries=self.retries
        )
        
        # Execute WALK
        results = []
        async for error_indication, error_status, error_index, var_binds in next_cmd(
            snmp_engine,
            auth_data,
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        ):
            if error_indication or error_status:
                break
            
            for var_bind in var_binds:
                oid_obj, val = var_bind
                oid_str = str(oid_obj)
                # Extract index from OID
                index = oid_str.split('.')[-1]
                results.append({
                    'oid': oid_str,
                    'index': index,
                    'value': val.prettyPrint()
                })
        
        return results
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test SNMP connectivity"""
        start_time = time.time()
        try:
            result = await self._snmp_get([OIDS['sysName']])
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'latency_ms': round(latency_ms, 2),
                'message': f"SNMP connection successful to {self.management_ip}",
                'sysName': result.get(OIDS['sysName'], 'Unknown')
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                'success': False,
                'latency_ms': round(latency_ms, 2),
                'message': f"SNMP connection failed: {str(e)}",
                'error_code': 'SNMP_ERROR'
            }
    
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get device system information via SNMP"""
        try:
            result = await self._snmp_get([
                OIDS['sysName'],
                OIDS['sysDescr'],
                OIDS['sysUpTime']
            ])
            
            # Parse uptime (in hundredths of seconds)
            uptime_ticks = int(result.get(OIDS['sysUpTime'], 0))
            uptime_seconds = uptime_ticks // 100
            
            return {
                'hostname': result.get(OIDS['sysName'], 'Unknown'),
                'description': result.get(OIDS['sysDescr'], 'Unknown'),
                'uptime_seconds': uptime_seconds,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error getting system info: {e}")
            return None
    
    async def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get list of interfaces via SNMP"""
        try:
            # Walk interface table
            if_names = await self._snmp_walk(OIDS['ifName'])
            if_descrs = await self._snmp_walk(OIDS['ifDescr'])
            if_admin_status = await self._snmp_walk(OIDS['ifAdminStatus'])
            if_oper_status = await self._snmp_walk(OIDS['ifOperStatus'])
            if_speed = await self._snmp_walk(OIDS['ifSpeed'])
            if_high_speed = await self._snmp_walk(OIDS['ifHighSpeed'])
            if_mtu = await self._snmp_walk(OIDS['ifMtu'])
            if_alias = await self._snmp_walk(OIDS['ifAlias'])
            
            # Build interface list
            interfaces = []
            for if_name in if_names:
                index = if_name['index']
                
                # Find matching entries
                descr = next((x for x in if_descrs if x['index'] == index), None)
                admin_status = next((x for x in if_admin_status if x['index'] == index), None)
                oper_status = next((x for x in if_oper_status if x['index'] == index), None)
                speed = next((x for x in if_speed if x['index'] == index), None)
                high_speed = next((x for x in if_high_speed if x['index'] == index), None)
                mtu = next((x for x in if_mtu if x['index'] == index), None)
                alias = next((x for x in if_alias if x['index'] == index), None)
                
                # Determine speed (prefer highSpeed if available)
                speed_bps = 0
                if high_speed and int(high_speed['value']) > 0:
                    speed_bps = int(high_speed['value']) * 1_000_000  # Mbps to bps
                elif speed:
                    speed_bps = int(speed['value'])
                
                interfaces.append({
                    'if_index': int(index),
                    'name': if_name['value'],
                    'description': descr['value'] if descr else '',
                    'alias': alias['value'] if alias else '',
                    'admin_status': 'up' if admin_status and admin_status['value'] == '1' else 'down',
                    'status': 'up' if oper_status and oper_status['value'] == '1' else 'down',
                    'speed_bps': speed_bps,
                    'mtu': int(mtu['value']) if mtu else None
                })
            
            return interfaces
        except Exception as e:
            print(f"Error getting interfaces: {e}")
            return []
    
    async def get_interface_statistics(self) -> List[Dict[str, Any]]:
        """Get interface traffic statistics via SNMP"""
        try:
            # Walk traffic counters (64-bit)
            if_hc_in = await self._snmp_walk(OIDS['ifHCInOctets'])
            if_hc_out = await self._snmp_walk(OIDS['ifHCOutOctets'])
            if_in_errors = await self._snmp_walk(OIDS['ifInErrors'])
            if_out_errors = await self._snmp_walk(OIDS['ifOutErrors'])
            if_in_discards = await self._snmp_walk(OIDS['ifInDiscards'])
            if_out_discards = await self._snmp_walk(OIDS['ifOutDiscards'])
            
            # Build statistics list
            stats = []
            for if_in in if_hc_in:
                index = if_in['index']
                
                out_octets = next((x for x in if_hc_out if x['index'] == index), None)
                in_errors = next((x for x in if_in_errors if x['index'] == index), None)
                out_errors = next((x for x in if_out_errors if x['index'] == index), None)
                in_discards = next((x for x in if_in_discards if x['index'] == index), None)
                out_discards = next((x for x in if_out_discards if x['index'] == index), None)
                
                stats.append({
                    'if_index': int(index),
                    'rx_bytes': int(if_in['value']),
                    'tx_bytes': int(out_octets['value']) if out_octets else 0,
                    'rx_errors': int(in_errors['value']) if in_errors else 0,
                    'tx_errors': int(out_errors['value']) if out_errors else 0,
                    'rx_discards': int(in_discards['value']) if in_discards else 0,
                    'tx_discards': int(out_discards['value']) if out_discards else 0,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return stats
        except Exception as e:
            print(f"Error getting interface statistics: {e}")
            return []
    
    async def close(self):
        """Cleanup SNMP engine"""
        self._snmp_engine = None

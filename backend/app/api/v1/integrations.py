"""
Zabbix Integration API
Foundation for Zabbix monitoring integration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import httpx

from ...core.database import get_db
from ...core.deps import get_current_user
from ...core.config import settings
from ...models import User

router = APIRouter(prefix="/integrations/zabbix", tags=["Integrations"])


class ZabbixClient:
    """Simple Zabbix API client"""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.api_url = f"{self.url}/api_json.php"
    
    async def _request(self, method: str, params: dict = None) -> dict:
        """Make Zabbix API request"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
            "auth": self.token
        }
        
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            response = await client.post(self.api_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(result['error'].get('data', 'Zabbix API error'))
            
            return result.get('result', {})
    
    async def test_connection(self) -> dict:
        """Test Zabbix connection"""
        try:
            result = await self._request("apiinfo.version")
            return {
                "success": True,
                "version": result,
                "message": f"Connected to Zabbix {result}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_hosts(self, limit: int = 100) -> list:
        """Get Zabbix hosts"""
        result = await self._request("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "limit": limit
        })
        return result
    
    async def get_problems(self, limit: int = 50) -> list:
        """Get active problems"""
        result = await self._request("problem.get", {
            "output": "extend",
            "recent": True,
            "limit": limit
        })
        return result


def get_zabbix_client() -> Optional[ZabbixClient]:
    """Get Zabbix client if configured"""
    if not settings.ZABBIX_URL or not settings.ZABBIX_API_TOKEN:
        return None
    return ZabbixClient(settings.ZABBIX_URL, settings.ZABBIX_API_TOKEN)


@router.get("/status")
async def get_zabbix_status(
    current_user: User = Depends(get_current_user)
):
    """Get Zabbix integration status"""
    client = get_zabbix_client()
    
    if not client:
        return {
            "configured": False,
            "message": "Zabbix integration not configured. Set ZABBIX_URL and ZABBIX_API_TOKEN in .env"
        }
    
    result = await client.test_connection()
    
    return {
        "configured": True,
        "url": settings.ZABBIX_URL,
        "connected": result.get("success", False),
        "version": result.get("version"),
        "message": result.get("message")
    }


@router.post("/test")
async def test_zabbix_connection(
    current_user: User = Depends(get_current_user)
):
    """Test Zabbix connection"""
    client = get_zabbix_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zabbix not configured. Set ZABBIX_URL and ZABBIX_API_TOKEN in .env"
        )
    
    result = await client.test_connection()
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("message", "Connection failed")
        )
    
    return result


@router.get("/hosts")
async def get_zabbix_hosts(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get hosts from Zabbix"""
    client = get_zabbix_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zabbix not configured"
        )
    
    try:
        hosts = await client.get_hosts(limit=limit)
        return {"hosts": hosts, "count": len(hosts)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get hosts: {str(e)}"
        )


@router.get("/problems")
async def get_zabbix_problems(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get active problems from Zabbix"""
    client = get_zabbix_client()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zabbix not configured"
        )
    
    try:
        problems = await client.get_problems(limit=limit)
        return {"problems": problems, "count": len(problems)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get problems: {str(e)}"
        )

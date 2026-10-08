"""
PNMP Schemas Package
Export all schemas for easy import
"""
from .schemas import (
    # Auth
    Token, TokenData, LoginRequest,
    
    # Users
    UserBase, UserCreate, UserUpdate, UserResponse, UserInDB,
    
    # Sites
    SiteBase, SiteCreate, SiteUpdate, SiteResponse,
    
    # Devices
    DeviceBase, DeviceCreate, DeviceUpdate, DeviceResponse,
    
    # Credentials
    DeviceCredentialCreate, DeviceCredentialSafeResponse,
    
    # Interfaces
    InterfaceResponse,
    
    # Connection Test
    TestConnectionResponse,
    
    # Alerts & Events
    AlertResponse, EventResponse,
    
    # Metrics
    DeviceMetricResponse, InterfaceMetricResponse,
    MetricsResponse, InterfaceMetricsResponse,
    
    # Dashboard
    DashboardSummary, DeviceStatusSummary,
    
    # Pagination
    PaginationInfo, PaginatedResponse,
    
    # Generic
    APIResponse
)

__all__ = [
    'Token', 'TokenData', 'LoginRequest',
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse', 'UserInDB',
    'SiteBase', 'SiteCreate', 'SiteUpdate', 'SiteResponse',
    'DeviceBase', 'DeviceCreate', 'DeviceUpdate', 'DeviceResponse',
    'DeviceCredentialCreate', 'DeviceCredentialSafeResponse',
    'InterfaceResponse',
    'TestConnectionResponse',
    'AlertResponse', 'EventResponse',
    'DeviceMetricResponse', 'InterfaceMetricResponse',
    'MetricsResponse', 'InterfaceMetricsResponse',
    'DashboardSummary', 'DeviceStatusSummary',
    'PaginationInfo', 'PaginatedResponse',
    'APIResponse'
]

"""
PNMP Database Seed Script
Creates initial data for development
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import User, UserRole, Site, Device, DeviceRole, DeviceStatus

def seed_database():
    """Seed database with initial data"""
    print("🌱 Starting database seed...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    db = SessionLocal()
    
    try:
        # Create admin user
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@pssn.ac.id",
                full_name="Super Administrator",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            print("✓ Created admin user (username: admin, password: admin123)")
        else:
            print("⊘ Admin user already exists")
        
        # Create demo users
        demo_users = [
            {"username": "neteng1", "email": "neteng1@pssn.ac.id", "full_name": "Network Engineer 1", "role": UserRole.NETWORK_ENGINEER},
            {"username": "operator1", "email": "operator1@pssn.ac.id", "full_name": "NOC Operator", "role": UserRole.OPERATOR},
            {"username": "viewer1", "email": "viewer1@pssn.ac.id", "full_name": "Viewer User", "role": UserRole.VIEWER},
        ]
        
        for user_data in demo_users:
            if not db.query(User).filter(User.username == user_data["username"]).first():
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=get_password_hash("password123"),
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
        print("✓ Created demo users (password: password123)")
        
        # Create sites
        sites_data = [
            {"name": "Data Center", "description": "Main data center facility"},
            {"name": "Gedung PSSN", "description": "Pusat Sistem dan Sumber Informasi Nasional"},
            {"name": "Gedung Akademik", "description": "Academic Building"},
            {"name": "Gedung Administrasi", "description": "Administration Building"},
            {"name": "Dormitory", "description": "Student Dormitory"},
            {"name": "Internet Gateway", "description": "ISP Gateway Point"},
        ]
        
        sites = {}
        for site_data in sites_data:
            if not db.query(Site).filter(Site.name == site_data["name"]).first():
                site = Site(**site_data)
                db.add(site)
                db.flush()
                sites[site_data["name"]] = site.id
            else:
                site = db.query(Site).filter(Site.name == site_data["name"]).first()
                sites[site_data["name"]] = site.id
        print("✓ Created demo sites")
        
        # Create demo devices
        devices_data = [
            {
                "hostname": "FG-200G-DC",
                "display_name": "FortiGate 200G",
                "management_ip": "10.0.0.1",
                "vendor": "Fortinet",
                "model": "FortiGate 200G",
                "device_type": "Firewall",
                "device_role": DeviceRole.FIREWALL,
                "site_id": sites["Data Center"],
                "location": "Rack A1",
                "status": DeviceStatus.UP,
                "description": "Main perimeter firewall",
                "is_demo": True
            },
            {
                "hostname": "ARUBA-CX-CORE",
                "display_name": "Aruba CX Core Switch",
                "management_ip": "10.1.0.1",
                "vendor": "Aruba",
                "model": "CX 8325",
                "device_type": "Switch",
                "device_role": DeviceRole.CORE_SWITCH,
                "site_id": sites["Gedung PSSN"],
                "location": "Floor 1, Rack A1",
                "status": DeviceStatus.UP,
                "description": "Core switch AOS-CX",
                "is_demo": True
            },
            {
                "hostname": "CCR-01",
                "display_name": "Cloud Core Router 01",
                "management_ip": "10.2.0.1",
                "vendor": "MikroTik",
                "model": "CCR2004",
                "device_type": "Router",
                "device_role": DeviceRole.ROUTER,
                "site_id": sites["Internet Gateway"],
                "location": "Rack C1",
                "status": DeviceStatus.UP,
                "description": "Core router ISP 1",
                "is_demo": True
            },
        ]
        
        for device_data in devices_data:
            if not db.query(Device).filter(Device.hostname == device_data["hostname"]).first():
                device = Device(**device_data)
                db.add(device)
        print("✓ Created demo devices")
        
        # Commit all changes
        db.commit()
        print("\n✅ Database seed completed successfully!")
        print("\n📋 Login credentials:")
        print("   Admin: admin / admin123")
        print("   Others: neteng1 / password123")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

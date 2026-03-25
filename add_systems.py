"""Add your source systems to database"""

from datetime import date, time
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, SLADefinitionModel

def add_systems():
    """Add source systems and SLA definitions"""
    init_db()
    
    # CUSTOMIZE THIS: Add your actual 20 source systems here
    # 
    # Configuration Guide:
    # - id: Unique identifier (uppercase, no spaces, e.g., "PROD_SALES")
    # - name: Human-readable name
    # - directory_path: Full path to monitored directory
    #   * Windows: Use double backslashes (\\) or raw strings (r"C:\path")
    #   * Linux/Mac: Use forward slashes (/path/to/directory)
    # - is_active: Set to False to temporarily disable monitoring
    # - expected_arrival_time: When files typically arrive (24-hour format)
    # - window_minutes: Tolerance window (±minutes from expected time)
    # - minimum_files_per_day: Minimum expected files per day
    
    systems = [
        # System 1: Sales Data
        {
            "id": "PROD_SALES",
            "name": "Production Sales System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\sales",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(9, 0, 0),  # 9:00 AM
                "window_minutes": 30,  # ±30 minutes (8:30 AM - 9:30 AM)
                "minimum_files_per_day": 5,
            }
        },
        
        # System 2: Inventory Data
        {
            "id": "PROD_INVENTORY",
            "name": "Production Inventory System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\inventory",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(10, 0, 0),  # 10:00 AM
                "window_minutes": 60,  # ±60 minutes
                "minimum_files_per_day": 3,
            }
        },
        
        # System 3: Customer Data
        {
            "id": "PROD_CUSTOMER",
            "name": "Production Customer System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\customer",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(8, 30, 0),  # 8:30 AM
                "window_minutes": 45,
                "minimum_files_per_day": 10,
            }
        },
        
        # System 4: Financial Data
        {
            "id": "PROD_FINANCE",
            "name": "Production Finance System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\finance",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(7, 0, 0),  # 7:00 AM
                "window_minutes": 15,  # Strict timing
                "minimum_files_per_day": 20,
            }
        },
        
        # System 5: HR Data
        {
            "id": "PROD_HR",
            "name": "Production HR System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\hr",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(11, 0, 0),  # 11:00 AM
                "window_minutes": 120,  # Flexible timing
                "minimum_files_per_day": 2,
            }
        },
        
        # System 6: Marketing Data
        {
            "id": "PROD_MARKETING",
            "name": "Production Marketing System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\marketing",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(14, 0, 0),  # 2:00 PM
                "window_minutes": 90,
                "minimum_files_per_day": 5,
            }
        },
        
        # System 7: Logistics Data
        {
            "id": "PROD_LOGISTICS",
            "name": "Production Logistics System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\logistics",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(6, 0, 0),  # 6:00 AM
                "window_minutes": 30,
                "minimum_files_per_day": 15,
            }
        },
        
        # System 8: Warehouse Data
        {
            "id": "PROD_WAREHOUSE",
            "name": "Production Warehouse System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\warehouse",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(12, 0, 0),  # 12:00 PM
                "window_minutes": 60,
                "minimum_files_per_day": 8,
            }
        },
        
        # System 9: Supplier Data
        {
            "id": "PROD_SUPPLIER",
            "name": "Production Supplier System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\supplier",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(9, 30, 0),  # 9:30 AM
                "window_minutes": 45,
                "minimum_files_per_day": 12,
            }
        },
        
        # System 10: Product Data
        {
            "id": "PROD_PRODUCT",
            "name": "Production Product System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\product",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(10, 30, 0),  # 10:30 AM
                "window_minutes": 60,
                "minimum_files_per_day": 6,
            }
        },
        
        # System 11: Order Data
        {
            "id": "PROD_ORDER",
            "name": "Production Order System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\order",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(8, 0, 0),  # 8:00 AM
                "window_minutes": 30,
                "minimum_files_per_day": 25,
            }
        },
        
        # System 12: Shipping Data
        {
            "id": "PROD_SHIPPING",
            "name": "Production Shipping System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\shipping",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(13, 0, 0),  # 1:00 PM
                "window_minutes": 60,
                "minimum_files_per_day": 10,
            }
        },
        
        # System 13: Returns Data
        {
            "id": "PROD_RETURNS",
            "name": "Production Returns System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\returns",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(15, 0, 0),  # 3:00 PM
                "window_minutes": 90,
                "minimum_files_per_day": 3,
            }
        },
        
        # System 14: Quality Control Data
        {
            "id": "PROD_QC",
            "name": "Production Quality Control System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\qc",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(11, 30, 0),  # 11:30 AM
                "window_minutes": 45,
                "minimum_files_per_day": 7,
            }
        },
        
        # System 15: Compliance Data
        {
            "id": "PROD_COMPLIANCE",
            "name": "Production Compliance System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\compliance",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(16, 0, 0),  # 4:00 PM
                "window_minutes": 120,
                "minimum_files_per_day": 2,
            }
        },
        
        # System 16: Analytics Data
        {
            "id": "PROD_ANALYTICS",
            "name": "Production Analytics System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\analytics",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(5, 0, 0),  # 5:00 AM
                "window_minutes": 30,
                "minimum_files_per_day": 15,
            }
        },
        
        # System 17: Reporting Data
        {
            "id": "PROD_REPORTING",
            "name": "Production Reporting System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\reporting",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(17, 0, 0),  # 5:00 PM
                "window_minutes": 60,
                "minimum_files_per_day": 5,
            }
        },
        
        # System 18: Integration Data
        {
            "id": "PROD_INTEGRATION",
            "name": "Production Integration System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\integration",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(12, 30, 0),  # 12:30 PM
                "window_minutes": 90,
                "minimum_files_per_day": 8,
            }
        },
        
        # System 19: Backup Data
        {
            "id": "PROD_BACKUP",
            "name": "Production Backup System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\backup",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(23, 0, 0),  # 11:00 PM
                "window_minutes": 60,
                "minimum_files_per_day": 1,
            }
        },
        
        # System 20: Archive Data
        {
            "id": "PROD_ARCHIVE",
            "name": "Production Archive System",
            "directory_path": "C:\\Users\\srinivas.susarapu\\Source_Data_Files\\archive",  # CHANGE THIS
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(22, 0, 0),  # 10:00 PM
                "window_minutes": 120,
                "minimum_files_per_day": 1,
            }
        },
    ]
    
    print("Adding source systems to database...")
    print("=" * 50)
    
    with get_db_session() as session:
        for sys_config in systems:
            # Check if exists
            existing = session.query(SourceSystemModel).filter_by(
                id=sys_config["id"]
            ).first()
            
            if existing:
                print(f"⚠️  System {sys_config['id']} already exists - skipping")
                continue
            
            # Create source system
            system = SourceSystemModel(
                id=sys_config["id"],
                name=sys_config["name"],
                directory_path=sys_config["directory_path"],
                is_active=sys_config["is_active"],
            )
            session.add(system)
            
            # Create SLA definition
            sla = SLADefinitionModel(
                source_system_id=sys_config["id"],
                expected_arrival_time=sys_config["sla"]["expected_arrival_time"],
                expected_arrival_window_minutes=sys_config["sla"]["window_minutes"],
                minimum_files_per_day=sys_config["sla"]["minimum_files_per_day"],
                weight=1.0,
                effective_from=date(2026, 1, 1),
                effective_to=None,
            )
            session.add(sla)
            
            print(f"✅ Added system: {sys_config['id']}")
            print(f"   Name: {sys_config['name']}")
            print(f"   Path: {sys_config['directory_path']}")
            print(f"   SLA: {sys_config['sla']['expected_arrival_time']} ±{sys_config['sla']['window_minutes']}min")
        
        session.commit()
    
    print("\n" + "=" * 50)
    print("✅ All systems configured!")
    print("\nNext steps:")
    print("  1. Verify directories exist")
    print("  2. Start monitoring: python start_monitoring.py")
    print("  3. Start API: python run_api.py")

if __name__ == "__main__":
    add_systems()

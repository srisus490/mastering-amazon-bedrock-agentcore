"""Check database for data"""

from src.database.connection import get_db_session, init_db
from src.database.models import FileArrivalModel, SourceSystemModel
from sqlalchemy import func

def check_data():
    """Check what data exists in the database"""
    
    # Initialize database connection
    init_db()
    
    with get_db_session() as session:
        # Check source systems
        system_count = session.query(SourceSystemModel).count()
        print(f"Source Systems: {system_count}")
        
        if system_count > 0:
            systems = session.query(SourceSystemModel).limit(5).all()
            print("\nFirst 5 systems:")
            for sys in systems:
                print(f"  - {sys.id} ({sys.name})")
        
        # Check file arrivals
        arrival_count = session.query(FileArrivalModel).count()
        print(f"\nFile Arrivals: {arrival_count}")
        
        if arrival_count > 0:
            # Count by system
            counts = session.query(
                FileArrivalModel.source_system_id,
                func.count(FileArrivalModel.id).label('count')
            ).group_by(FileArrivalModel.source_system_id).all()
            
            print("\nFile arrivals by system:")
            for system_id, count in counts[:10]:
                print(f"  - {system_id}: {count} files")
            
            # Show date range
            first = session.query(func.min(FileArrivalModel.arrival_timestamp)).scalar()
            last = session.query(func.max(FileArrivalModel.arrival_timestamp)).scalar()
            print(f"\nDate range: {first} to {last}")
        else:
            print("\nNo file arrivals in database!")
            print("Run 'python start_monitoring.py' to generate data")

if __name__ == "__main__":
    try:
        check_data()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

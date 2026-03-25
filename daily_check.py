"""Daily health check script"""

from datetime import date, datetime
from src.database.connection import init_db, get_db_session
from src.database.models import FileArrivalModel, SLAViolationModel, SourceSystemModel
from src.sla.calculator import ScoreCalculator

def daily_check():
    """Run daily health check"""
    
    init_db()
    
    print("\n" + "=" * 60)
    print("📊 DAILY HEALTH CHECK")
    print("=" * 60)
    print(f"Date: {date.today().strftime('%Y-%m-%d %A')}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    # Check file arrivals today
    print("\n📁 FILE ARRIVALS TODAY")
    print("-" * 60)
    with get_db_session() as session:
        from datetime import datetime as dt
        today_start = dt.combine(date.today(), dt.min.time())
        
        # Total count
        total_count = session.query(FileArrivalModel).filter(
            FileArrivalModel.arrival_timestamp >= today_start
        ).count()
        print(f"Total files detected: {total_count}")
        
        # By system
        systems = session.query(SourceSystemModel).filter_by(is_active=True).all()
        for sys in systems:
            _ = (sys.id, sys.name)
            session.expunge(sys)
            
            count = session.query(FileArrivalModel).filter(
                FileArrivalModel.source_system_id == sys.id,
                FileArrivalModel.arrival_timestamp >= today_start
            ).count()
            
            print(f"  {sys.id}: {count} files")
    
    # Check SLA violations
    print("\n⚠️  SLA VIOLATIONS TODAY")
    print("-" * 60)
    with get_db_session() as session:
        violations = session.query(SLAViolationModel).filter(
            SLAViolationModel.violation_date == date.today()
        ).all()
        
        if violations:
            print(f"Found {len(violations)} violation(s):")
            for v in violations:
                _ = (v.id, v.source_system_id, v.violation_type, v.severity)
                session.expunge(v)
                print(f"  {v.source_system_id}: {v.violation_type} ({v.severity})")
        else:
            print("✅ No violations today")
    
    # Check SLA scores
    print("\n📈 SLA SCORES")
    print("-" * 60)
    calculator = ScoreCalculator()
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).filter_by(
            is_active=True
        ).all()
        
        for sys in systems:
            _ = (sys.id, sys.name)
            session.expunge(sys)
            
            score = calculator.calculate_daily_score(sys.id, date.today())
            
            # Status indicator
            if score >= 90:
                status = "✅ EXCELLENT"
            elif score >= 70:
                status = "⚠️  WARNING"
            else:
                status = "❌ CRITICAL"
            
            print(f"  {sys.id}: {score:.1f}/100 {status}")
    
    # Database size
    print("\n💾 DATABASE INFO")
    print("-" * 60)
    from pathlib import Path
    db_file = Path("data/file_monitoring.db")
    if db_file.exists():
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"Database size: {size_mb:.2f} MB")
        
        # Record count
        with get_db_session() as session:
            total_files = session.query(FileArrivalModel).count()
            total_violations = session.query(SLAViolationModel).count()
            print(f"Total file records: {total_files:,}")
            print(f"Total violations: {total_violations:,}")
    
    print("\n" + "=" * 60)
    print("✅ Health check complete!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    daily_check()

"""Simulate file arrivals for testing and demos."""

import random
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.database.connection import get_db_session
from src.database.models import FileArrivalModel, SourceSystemModel

router = APIRouter()

FILE_TEMPLATES = {
    "PROD_SALES":       ("sales_daily_{date}_{i}.csv", "id,timestamp,order_id,amount,status"),
    "PROD_INVENTORY":   ("inventory_snapshot_{date}_{i}.csv", "id,sku,quantity,location,updated_at"),
    "PROD_CUSTOMER":    ("customer_export_{date}_{i}.csv", "id,customer_id,email,segment,region"),
    "PROD_FINANCE":     ("finance_ledger_{date}_{i}.csv", "id,account,debit,credit,posting_date"),
    "PROD_HR":          ("hr_headcount_{date}_{i}.csv", "id,employee_id,department,status,date"),
    "PROD_MARKETING":   ("campaign_metrics_{date}_{i}.csv", "id,campaign_id,impressions,clicks,spend"),
    "PROD_LOGISTICS":   ("logistics_events_{date}_{i}.csv", "id,shipment_id,status,location,eta"),
    "PROD_WAREHOUSE":   ("warehouse_movements_{date}_{i}.csv", "id,item_id,from_loc,to_loc,qty"),
    "PROD_SUPPLIER":    ("supplier_feed_{date}_{i}.csv", "id,supplier_id,po_number,items,value"),
    "PROD_PRODUCT":     ("product_catalog_{date}_{i}.csv", "id,sku,name,category,price"),
    "PROD_ORDER":       ("orders_{date}_{i}.csv", "id,order_id,customer_id,total,status"),
    "PROD_SHIPPING":    ("shipping_manifest_{date}_{i}.csv", "id,tracking_id,carrier,dest,weight"),
    "PROD_RETURNS":     ("returns_report_{date}_{i}.csv", "id,return_id,order_id,reason,amount"),
    "PROD_QC":          ("qc_inspection_{date}_{i}.csv", "id,batch_id,pass_rate,defects,inspector"),
    "PROD_COMPLIANCE":  ("compliance_audit_{date}_{i}.csv", "id,rule_id,status,evidence,reviewed_by"),
    "PROD_ANALYTICS":   ("analytics_export_{date}_{i}.csv", "id,metric,value,dimension,period"),
    "PROD_REPORTING":   ("daily_report_{date}_{i}.csv", "id,report_id,category,rows,generated_at"),
    "PROD_INTEGRATION": ("integration_log_{date}_{i}.csv", "id,source,target,records,status"),
    "PROD_BACKUP":      ("backup_manifest_{date}_{i}.txt", "backup_id,size_gb,duration_min,status"),
    "PROD_ARCHIVE":     ("archive_index_{date}_{i}.txt", "archive_id,files,size_gb,retention_days"),
}


class SimulateRequest(BaseModel):
    system_ids: Optional[List[str]] = None  # None = all active systems
    files_per_system: int = 3
    arrival_offset_minutes: int = 0  # positive = late, negative = early


class SimulateResponse(BaseModel):
    inserted: int
    systems: List[str]
    timestamp: str


@router.post("", response_model=SimulateResponse)
async def simulate_file_arrivals(req: SimulateRequest):
    """
    Inject synthetic file arrival records into the database.
    Useful for demos and testing without real file transfers.
    """
    files_per_system = max(1, min(req.files_per_system, 50))
    now = datetime.utcnow()

    with get_db_session() as session:
        if req.system_ids:
            systems = session.query(SourceSystemModel).filter(
                SourceSystemModel.id.in_(req.system_ids),
                SourceSystemModel.is_active == True,
            ).all()
        else:
            systems = session.query(SourceSystemModel).filter(
                SourceSystemModel.is_active == True
            ).all()

        system_ids = [s.id for s in systems]

        records = []
        date_str = now.strftime("%Y%m%d")
        for sid in system_ids:
            tmpl_file, _ = FILE_TEMPLATES.get(sid, (f"{sid.lower()}_{{date}}_{{i}}.csv", "id,value"))
            for i in range(files_per_system):
                offset_min = req.arrival_offset_minutes + random.randint(-5, 5)
                arrival_ts = now + timedelta(minutes=offset_min, seconds=random.randint(0, 59))
                fname = tmpl_file.format(date=date_str, i=i)
                record = FileArrivalModel(
                    source_system_id=sid,
                    filename=fname,
                    file_path=f"/data/sources/{sid.lower()}/{fname}",
                    arrival_timestamp=arrival_ts,
                    file_size_bytes=random.randint(4096, 5_242_880),
                )
                session.add(record)
                records.append(record)

        session.commit()

    return SimulateResponse(
        inserted=len(records),
        systems=system_ids,
        timestamp=now.isoformat(),
    )

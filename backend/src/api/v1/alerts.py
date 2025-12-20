"""
Alerts API endpoints.
Manage user-defined stock alerts.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.logging import get_logger
from ...models.database import Alert
from ...models.schemas import (
    AlertCreate,
    AlertUpdate,
    AlertResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=AlertResponse, status_code=201)
def create_alert(
    alert: AlertCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create a new alert rule.
    
    Args:
        alert: Alert configuration
        db: Database session
        
    Returns:
        Created alert
    """
    db_alert = Alert(
        name=alert.name,
        description=alert.description,
        alert_type=alert.alert_type,
        conditions=alert.conditions,
        stock_symbols=alert.stock_symbols,
        notification_channels=alert.notification_channels,
        notification_config=alert.notification_config,
        is_active=alert.is_active
    )
    
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    logger.info(f"Created alert: {db_alert.name} (ID: {db_alert.id})")
    
    return db_alert


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List all alert rules.
    
    Args:
        active_only: Filter to only active alerts
        db: Database session
        
    Returns:
        List of alerts
    """
    query = db.query(Alert)
    
    if active_only:
        query = query.filter(Alert.is_active == True)
    
    alerts = query.all()
    
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific alert by ID.
    
    Args:
        alert_id: Alert ID
        db: Database session
        
    Returns:
        Alert details
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update an existing alert.
    
    Args:
        alert_id: Alert ID
        alert_update: Updated alert data
        db: Database session
        
    Returns:
        Updated alert
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    # Update fields if provided
    update_data = alert_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    db.commit()
    db.refresh(alert)
    
    logger.info(f"Updated alert: {alert.name} (ID: {alert.id})")
    
    return alert


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an alert.
    
    Args:
        alert_id: Alert ID
        db: Database session
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    db.delete(alert)
    db.commit()
    
    logger.info(f"Deleted alert: {alert.name} (ID: {alert_id})")
    
    return None

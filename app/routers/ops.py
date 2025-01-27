from fastapi import Depends, HTTPException, status, APIRouter 
from utils import TaskAnalytics, TaskNotifier, TaskScheduler
from database import get_db
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
from fastapi.responses import StreamingResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(tags=["ops"], prefix="/ops")


@router.get("/schedule", response_model=List[Dict])
def schedule_tasks(db: Session = Depends(get_db)):
    """Schedule pending tasks based on priority and due dates"""
    try:
        scheduler = TaskScheduler(db)
        scheduled_tasks = scheduler.schedule_tasks()
        return scheduled_tasks
    except Exception as e:
        logger.error(f"Error scheduling tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule tasks"
        )

@router.get("/notify", response_model=List[Dict])
def send_task_notifications(db: Session = Depends(get_db)):
    """Send notifications for upcoming and overdue tasks"""
    try:
        notifier = TaskNotifier(db)
        notifications = notifier.send_notifications()
        return notifications
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notifications"
        )

@router.get("/statistics", response_model=Dict)
def get_task_statistics(db: Session = Depends(get_db)):
    """Get task statistics and analytics"""
    try:
        analytics = TaskAnalytics(db)
        statistics = analytics.get_task_statistics()
        return statistics
    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate statistics"
        )

@router.get("/report", response_model=Dict)
def generate_task_report(db: Session = Depends(get_db)):
    """Generate detailed task analysis report"""
    try:
        analytics = TaskAnalytics(db)
        report = analytics.generate_task_report()
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )
    
@router.get("/download_csv")
def download_csv(db: Session = Depends(get_db)):
    analytics = TaskAnalytics(db)
    csv_buffer = analytics.export_tasks_to_csv()

    return StreamingResponse(
        content=csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=task_data.csv"}
    )
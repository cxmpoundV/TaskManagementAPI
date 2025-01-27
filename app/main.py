from fastapi import FastAPI
from database import engine, SessionLocal
from utils import TaskNotifier
import models
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from contextlib import asynccontextmanager
from routers import ops,user,task,auth

models.Base.metadata.create_all(bind = engine)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


notification_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global notification_scheduler
    try:
        # db = SessionLocal()
        # Create background scheduler for daily notifications
        notification_scheduler = BackgroundScheduler()
        
        def send_daily_notifications():
            with SessionLocal() as temp_db:
                notifier = TaskNotifier(temp_db)
                notifier.send_notifications()
        
        # Schedule daily notification job
        notification_scheduler.add_job(send_daily_notifications, 'interval', hours=24)
        notification_scheduler.start()
        
        logger.info("Background notification scheduler started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}")
        raise
    finally:
        
        if notification_scheduler:
            notification_scheduler.shutdown(wait=False)
            logger.info("Background scheduler shutdown successfully")


app = FastAPI(
    title="Task Management System",
    lifespan=lifespan
)


app.include_router(ops.router)
app.include_router(task.router)
app.include_router(user.router)
app.include_router(auth.router)



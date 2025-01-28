from models import TaskDB
from sqlalchemy.orm import Session
from models import TaskDB
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Dict
import models
from sqlalchemy import func
import pandas as pd
from io import StringIO
import bcrypt
import matplotlib.pyplot as plt
import logging 
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hash_password(password : str):
    return bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

def verify(plain_pass, hash_pass):
    return bcrypt.checkpw(plain_pass.encode('utf-8'), hash_pass)


class Taskutils:

    def __init__(self,db : Session) :
        self.db = db

    def update_task_status(self, task_id: int, status: str):
        task = self.db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
        if task:
            task.status = status
            self.db.commit()
            return task
        return None

    def update_due_date(self, task_id: int, due_date: str):
        task = self.db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
        if task:
            task.due_date = due_date
            self.db.commit()
            return task
        return None
    
class TaskAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def get_task_statistics(self) -> Dict:
        """Calculate various task statistics"""
        total_tasks = self.db.query(models.TaskDB).count()
        overdue_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.due_date < datetime.now(),
            models.TaskDB.status != "completed"
        ).count()
        
        # Calculate average completion time
        completed_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.status == "completed",
            models.TaskDB.completed_date.isnot(None)
        ).all()
        
        total_completion_time = timedelta()
        for task in completed_tasks:
            if task.completed_date and task.due_date:
                total_completion_time += task.completed_date - task.due_date
                
        avg_completion_time = (total_completion_time / len(completed_tasks) if completed_tasks 
                             else timedelta())

        # Tasks by priority
        priority_distribution = dict(
            self.db.query(
                models.TaskDB.priority,
                func.count(models.TaskDB.task_id)
            ).group_by(models.TaskDB.priority).all()
        )

        return {
            "total_tasks": total_tasks,
            "overdue_tasks": overdue_tasks,
            "completed_tasks": len(completed_tasks),
            "average_completion_time_days": avg_completion_time.days,
            "priority_distribution": priority_distribution
        }
    def export_tasks_to_csv(self):
        """Stream large task data as a CSV file."""
        # Fetch all tasks
        tasks = self.db.query(models.TaskDB).all()

        # Convert tasks to DataFrame
        task_data = [
            {
                "task_id": task.task_id,
                "name": task.name,
                "description": task.description,
                "status": task.status,
                "due_date": task.due_date,
                "completed_date": task.completed_date,
                "assigned_to": task.assigned_to,
                "priority": task.priority
            }
            for task in tasks
        ]
        df = pd.DataFrame(task_data)

        self.generate_visualizations(df)
        logger.info("Generating Visualizations")

        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)  
        return buffer

    def generate_task_report(self) -> Dict:
        """Generate detailed task analysis report"""
        current_date = datetime.now()
        
        # Tasks due this week
        week_end = current_date + timedelta(days=7)
        upcoming_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.due_date.between(current_date, week_end)
        ).all()

        # Tasks by status
        status_counts = dict(
            self.db.query(
                models.TaskDB.status,
                func.count(models.TaskDB.task_id)
            ).group_by(models.TaskDB.status).all()
        )

        return {
            "upcoming_tasks": [
                {
                    "name": task.name,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority
                } for task in upcoming_tasks
            ],
            "status_distribution": status_counts,
            "statistics": self.get_task_statistics()
        }
    
    def generate_visualizations(self, df: pd.DataFrame):
        """Generate visualizations and save them as files."""
        
        priority_counts = df["priority"].value_counts()
        plt.figure(figsize=(8, 6))
        priority_counts.plot.pie(autopct="%1.1f%%", startangle=90, title="Task Priority Distribution")
        plt.ylabel("")  
        plt.savefig("priority_distribution.png")
        plt.close()

        
        status_counts = df["status"].value_counts()
        plt.figure(figsize=(8, 6))
        status_counts.plot.bar(title="Task Status Distribution")
        plt.xlabel("Status")
        plt.ylabel("Count")
        plt.savefig("task_status_chart.png")
        plt.close()
    
class TaskScheduler:
    def __init__(self, db: Session):
        self.db = db

    def schedule_tasks(self) -> List[Dict]:
        """Schedule tasks based on priority and due dates"""
        # Get all pending tasks
        pending_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.status == "pending"
        ).order_by(
            models.TaskDB.priority.desc(),
            models.TaskDB.due_date.asc()
        ).all()

        scheduled_tasks = []
        current_date = datetime.now()

        for task in pending_tasks:
            # Calculate suggested start date based on priority
            if task.priority == "high":
                start_date = current_date
            elif task.priority == "medium":
                start_date = current_date + timedelta(days=1)
            else:
                start_date = current_date + timedelta(days=2)

            scheduled_tasks.append({
                "task_id": task.task_id,
                "name": task.name,
                "suggested_start_date": start_date.isoformat(),
                "due_date": task.due_date.isoformat(),
                "priority": task.priority
            })

        return scheduled_tasks

class TaskNotifier:
    def __init__(self, db: Session):
        self.db = db
        self.smtp_config = {
            'port': 587,
            'smtp_server': "smtp.mailosaur.net",
            'login': os.getenv("USERNAME"),
            'password': os.getenv("PASSWORD"),
            'sender_email': os.getenv("SENDER_MAIL")
        }

    def send_notifications(self, email) -> List[Dict]:
        """Send notifications for upcoming and overdue tasks"""

        self.smtp_config.update({'receiver_email' : email})
        current_date = datetime.now()
        notification_window = current_date + timedelta(days=2)

        # Get tasks due soon
        upcoming_tasks = self.db.query(models.TaskDB)\
        .join(models.User,models.TaskDB.owner_id == models.User.id)\
        .filter(
            models.TaskDB.due_date <= notification_window,
            models.TaskDB.status == "pending",
            models.User.email == email
        ).all()

        notifications = []

        message = ""

        for task in upcoming_tasks:
            days_until_due = (task.due_date - current_date).days
            
            message += "Task Details:\n\n"
            if days_until_due < 0:
                message += f"OVERDUE: Task '{task.name}' was due {abs(days_until_due)} days ago\n\n"
            else:
                message += f"REMINDER: Task '{task.name}' is due in {days_until_due} days\n\n"

            notifications.append({
                "task_id": task.task_id,
                "message": message,
                "sent_at": current_date.isoformat()
            })
        
        if len(message) > 0:
            self._send_email(message)

        return notifications

    def _send_email(self, content: str):
        message = MIMEText(content, "plain")
        message["Subject"] = "Task Notification"
        message["From"] = self.smtp_config['sender_email']
        message["To"] = self.smtp_config['receiver_email']

        with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['port']) as server:
            server.starttls()
            server.login(self.smtp_config['login'], self.smtp_config['password'])
            server.sendmail(
                self.smtp_config['sender_email'],
                self.smtp_config['receiver_email'],
                message.as_string()
            )


# class Reminder:
#     def __init__(self, db: Session = None):
#         self.db = db
#         self.smtp_config = {
#             'port': 587,
#             'smtp_server': "smtp.mailosaur.net",
#             'login': "bvbjq4xj@mailosaur.net",
#             'password': "vOkKLheznHlZanWCtSVEtxN0nnr9RlH5",
#             'sender_email': "promised-clock@bvbjq4xj.mailosaur.net",
#             'receiver_email': "expression-today@htdweext.mailosaur.net"
#         }

#     def get_reminder(self, content: str = None):
#         if content is None and self.db:
#             content = self._generate_default_content()
            
#         if not content:
#             raise ValueError("Email content is required when db is not provided")

#         message = MIMEText(content, "plain")
#         message["Subject"] = "Task Reminder Notification"
#         message["From"] = self.smtp_config['sender_email']
#         message["To"] = self.smtp_config['receiver_email']

#         with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['port']) as server:
#             server.starttls()
#             server.login(self.smtp_config['login'], self.smtp_config['password'])
#             server.sendmail(
#                 self.smtp_config['sender_email'],
#                 self.smtp_config['receiver_email'],
#                 message.as_string()
#             )

#     def _generate_default_content(self) -> str:
#         if not self.db:
#             return None
            
#         pending_tasks = self.db.query(TaskDB).filter(TaskDB.status == "pending").all()
#         if not pending_tasks:
#             return "No pending tasks found."
            
#         content = "Pending Tasks:\n\n"
#         for task in pending_tasks:
#             content += f"- {task.name} (Due: {task.due_date})\n"
#         return content


# class Scheduler(Reminder):
#     def __init__(self, db: Session):
#         super().__init__(db)
#         self.scheduler = BackgroundScheduler()
        
#     def start(self):
#         """Start the scheduler with configured jobs"""
#         self.scheduler.add_job(self.schedule, 'interval', hours=24)
#         self.scheduler.start()
        
#     def stop(self):
#         """Safely shut down the scheduler"""
#         self.scheduler.shutdown()

#     def schedule(self):
#         try:

#             due_soon = self.db.query(TaskDB).filter(
#                 TaskDB.due_date <= datetime.now() + timedelta(days=1),
#                 TaskDB.status == "pending"
#             ).all()

#             if not due_soon:
#                 return

#             email_content = self.generate_email_content(due_soon)
#             self.get_reminder(email_content)
            
#         except Exception as e:
#             print(f"Error in scheduler: {e}")

#     def generate_email_content(self, due_tasks) -> str:
#         content = "Task Reminder\n\n"
#         content += "Tasks Due in the Next 24 Hours:\n"
        
#         for task in due_tasks:
#             time_until_due = task.due_date - datetime.now()
#             hours_until_due = int(time_until_due.total_seconds() / 3600)
            
#             content += (
#                 f"- {task.name}\n"
#                 f"  Due: {task.due_date}\n"
#                 f"  Time remaining: {hours_until_due} hours\n\n"
#             )
            
#         return content
        
        

# class GetReport:

#     def __init__(self, db : Session):
#         self.db = db

#     def get_reports(self):

#         df = pd.read_sql_query(sql=select(TaskDB), con = engine)

#         df.to_csv("file.csv")


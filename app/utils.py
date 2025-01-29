from models import TaskDB
from sqlalchemy.orm import Session
from models import TaskDB
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import models
from sqlalchemy import func
import pandas as pd
from io import StringIO,BytesIO
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

    def get_task_statistics(self, user_id: int) -> Dict:
        """Calculate various task statistics for a specific user
        
        Args:
            user_id: The ID of the user to get statistics for
        """
        # Update total tasks query to filter by user
        total_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.owner_id == user_id
        ).count()
        
        overdue_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.due_date < datetime.now(),
            models.TaskDB.status != "completed",
            models.TaskDB.owner_id == user_id
        ).count()
        
        # Update completed tasks query to filter by user
        completed_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.status == "completed",
            models.TaskDB.completed_date.isnot(None),
            models.TaskDB.owner_id == user_id
        ).all()
        
        total_completion_time = timedelta()
        for task in completed_tasks:
            if task.completed_date and task.due_date:
                total_completion_time += task.completed_date - task.due_date
                
        avg_completion_time = (total_completion_time / len(completed_tasks) if completed_tasks 
                             else timedelta())

        # Update priority distribution query to filter by user
        priority_distribution = dict(
            self.db.query(
                models.TaskDB.priority,
                func.count(models.TaskDB.task_id)
            ).filter(models.TaskDB.owner_id == user_id)
            .group_by(models.TaskDB.priority).all()
        )

        return {
            "total_tasks": total_tasks,
            "overdue_tasks": overdue_tasks,
            "completed_tasks": len(completed_tasks),
            "average_completion_time_days": avg_completion_time.days,
            "priority_distribution": priority_distribution
        }
    def export_tasks_to_csv(self, user_id: int) -> Tuple[pd.DataFrame, StringIO]:
        """
        Export tasks to CSV and return both DataFrame and CSV buffer
        
        Args:
            user_id: The ID of the user whose tasks to export
        
        Returns:
            Tuple containing (DataFrame, StringIO buffer with CSV data)
        """
        # Fetch all tasks
        tasks = self.db.query(TaskDB).filter(TaskDB.owner_id == user_id).all()

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
                "priority": task.priority,
                "owner_id": task.owner_id
            }
            for task in tasks
        ]
        df = pd.DataFrame(task_data)

        # Create CSV buffer
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        
        return df, buffer

    def generate_task_report(self, user_id: int) -> Dict:
        """Generate detailed task analysis report for a specific user
        
        Args:
            user_id: The ID of the user to generate the report for
        """
        current_date = datetime.now()
        
        # Tasks due this week
        week_end = current_date + timedelta(days=7)
        upcoming_tasks = self.db.query(models.TaskDB).filter(
            models.TaskDB.due_date.between(current_date, week_end),
            models.TaskDB.owner_id == user_id
        ).all()

        # Tasks by status with user filtering
        status_counts = dict(
            self.db.query(
                models.TaskDB.status,
                func.count(models.TaskDB.task_id)
            ).filter(models.TaskDB.owner_id == user_id)
            .group_by(models.TaskDB.status).all()
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
            "statistics": self.get_task_statistics(user_id)  # Pass user_id here
        }
    
    def generate_visualizations(self, user_id: int) -> BytesIO:
        """
        Generate visualizations of task data
        
        Args:
            user_id: The ID of the user whose tasks to visualize
        
        Returns:
            BytesIO buffer containing the PNG image
        """
        # Get DataFrame directly without CSV conversion
        df, _ = self.export_tasks_to_csv(user_id)

        # Create visualization
        priority_counts = df["priority"].value_counts()
        plt.figure(figsize=(8, 6))
        plt.pie(priority_counts.values, labels=priority_counts.index, autopct="%1.1f%%", startangle=90)
        plt.title("Task Priority Distribution")
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()  # Close the figure to free memory
        buffer.seek(0)
        
        return buffer

        
        # status_counts = df["status"].value_counts()
        # plt.figure(figsize=(8, 6))
        # status_counts.plot.bar(title="Task Status Distribution")
        # plt.xlabel("Status")
        # plt.ylabel("Count")
        # plt.savefig("task_status_chart.png")
        # plt.close()
    
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
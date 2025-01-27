from fastapi import Depends, HTTPException, status, APIRouter, Response
from database import get_db
from utils import Taskutils
from schemas import TaskModel,TaskCreate,UpdateDueDate,UpdateStatus
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import models
from oauth2 import get_current_user


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["task"],prefix="/task")


@router.get("/", response_model=List[TaskModel])
async def get_tasks(db: Session = Depends(get_db),user_id : int = Depends(get_current_user)):
    try:
        tasks = db.query(models.TaskDB).all()
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db), user_id : int = Depends(get_current_user)):
    try:
        new_task = models.TaskDB(**task.model_dump())
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return {"message": "Task created", "task_id": new_task.task_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )

@router.put("/{id}")
def update_task(id : int, task : TaskModel, db : Session = Depends(get_db), user_id : int = Depends(get_current_user)):
    
    query = db.query(models.TaskDB).filter(models.TaskDB.task_id == id)

    updated_task = query.first()

    if not updated_task:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id : {id} does not exist")
    
    query.update(task.model_dump(), synchronize_session = False)

    db.commit()

    return {"data" : "successful"}



@router.delete("/{id}")
def delete_task(id : int, db : Session = Depends(get_db),user_id : int = Depends(get_current_user)):

    task = db.query(models.TaskDB).filter(models.TaskDB.task_id == id)

    if task.first() == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id : {id} does not exist")
    

    task.delete(synchronize_session = False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/update_task_status")
def update_status(new_task : UpdateStatus, db : Session = Depends(get_db)):

    taskutil = Taskutils(db)

    new_task.task_id = int(new_task.task_id)

    updated_task = taskutil.update_task_status(**new_task.model_dump())

    if updated_task is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return Response(status_code=status.HTTP_201_CREATED)

@router.put("/update_task_due_date")
def update_due_date(new_task : UpdateDueDate, db : Session = Depends(get_db)):

    taskutil = Taskutils(db)

    new_task.task_id = int(new_task.task_id)

    updated_task = taskutil.update_due_date(**new_task.model_dump())

    if updated_task is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return Response(status_code=status.HTTP_201_CREATED)
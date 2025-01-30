from fastapi import Depends, HTTPException, status, APIRouter, Response
from fastapi.responses import JSONResponse
from database import get_db
from utils import Taskutils
from schemas import TaskModel,TaskCreate,UpdateDueDate,UpdateStatus,UpdateStatusResponse,UpdateDueDateResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import models
from oauth2 import get_current_user
from notify import push_notifications


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["task"],prefix="/task")


@router.get("/", response_model=List[TaskModel])
def get_tasks(db: Session = Depends(get_db),
              current_user: int = Depends(get_current_user)):
    try:

        fill_na_func = Taskutils(db)
        fill_na_func.handle_db_data()

        tasks = db.query(models.TaskDB).filter(models.TaskDB.owner_id == current_user.id).all()

        push_notifications(current_user.email, "fetch-tasks", {"message" : "Fetched Tasked Successfully."})

        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, 
                db: Session = Depends(get_db), 
                current_user : int = Depends(get_current_user)):
    try:
        new_task = models.TaskDB(owner_id = current_user.id, **task.model_dump())
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
def update_task(id : int, task : TaskModel, 
                db : Session = Depends(get_db), 
                current_user : int = Depends(get_current_user)):
    
    query = db.query(models.TaskDB).filter(models.TaskDB.task_id == id,
                                           models.TaskDB.owner_id == current_user.id)

    updated_task = query.first()

    if not updated_task:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id : {id} does not exist")
    
    query.update(task.model_dump(), synchronize_session = False)

    db.commit()

    return {"data" : "successful"}



@router.delete("/{id}")
def delete_task(id : int, 
                db : Session = Depends(get_db),
                current_user : int = Depends(get_current_user)):

    task = db.query(models.TaskDB).filter(models.TaskDB.task_id == id,
                                          models.TaskDB.owner_id == current_user.id)

    if task.first() == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id : {id} does not exist")
    

    task.delete(synchronize_session = False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/update_status/{task_id}", response_model = UpdateStatusResponse)
def update_status(
    task_id: int,
    status_update: UpdateStatus,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    taskutil = Taskutils(db)
    
    updated_task = taskutil.update_task_status(
        task_id=task_id,
        owner_id = current_user.id,
        status=status_update.status
    )
    
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return JSONResponse(
    content={
        "task_id": updated_task.task_id,
        "name": updated_task.name,
        "status": updated_task.status
    },
    status_code=status.HTTP_201_CREATED
)

@router.put("/update_task_due_date/{task_id}", response_model = UpdateDueDateResponse)
def update_due_date(
    task_id: int,
    due_date_update: UpdateDueDate,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    taskutil = Taskutils(db)
    
    updated_task = taskutil.update_due_date(
        task_id=task_id,
        owner_id = current_user.id,
        due_date=due_date_update.due_date
    )
    
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return JSONResponse(
    content={
        "task_id": updated_task.task_id,
        "name": updated_task.name,
        "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None
    },
    status_code=status.HTTP_201_CREATED
)
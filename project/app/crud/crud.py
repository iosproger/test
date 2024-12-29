from typing import List

from sqlalchemy.orm import Session

from project.app.schemas import schemas
from project.app.models.models import User, Contract, Task, AssingCt, ActionTask, Notification
from passlib.context import CryptContext
from sqlalchemy import and_, not_


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_name(db: Session, user_name: str):
    return db.query(User).filter(User.user_name == user_name).first()



def create_user(db: Session,user_name:str, name: str, phone_number: str, email: str ,hashed_password: bytes, active: bool):
    new_user = User(user_name=user_name,name=name,phone_number=phone_number,email = email, hashed_password=hashed_password, active=active)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, name: str, password: str):
    user = get_user_by_name(db, name)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def user_check( db: Session ,user_name : str = None) -> bool:

    if not (user := get_user_by_name(db=db,user_name=user_name)):
        return False

    return True


# contract
def get_contract_by_id(db: Session, contract_id: int):
    try:
        return db.query(Contract).filter(Contract.contract_id == contract_id).first()
    except Exception as e:
        raise Exception(f"An error occurred while find contract by contract_id : {e}")

def get_tasks_by_ct_id(db: Session, contract_id: int):
    try:
        return db.query(Task).filter(Task.contract_id == contract_id).all()
    except Exception as e:
        raise Exception(f"An error occurred while fetching tasks by contract_id: {e}")
    
def get_all_contracts_except_assigned_and_user(db: Session, user_id: int):
    try:
        # Subquery to fetch all contract IDs assigned to the user
        assigned_ct_ids = db.query(AssingCt.contract_id).filter(AssingCt.user_id == user_id).subquery()

        # Main query to get contracts not owned by the user and not assigned to the user
        contracts = (
            db.query(Contract)
            .filter(
                and_(
                    Contract.owner_create_id != user_id,       # Exclude contracts owned by the user
                    not_(Contract.contract_id.in_(assigned_ct_ids))  # Exclude assigned contracts
                )
            )
            .all()
        )

        return contracts
    except Exception as e:
        raise Exception(f"An error occurred while fetching all contracts: {e}")    

def get_all_contracts(db: Session):
    try:
        return db.query(Contract).all()  # Fetch all contracts
    except Exception as e:
        raise Exception(f"An error occurred while fetching all contracts: {e}")


def create_contract(db: Session ,owner_create_id: int, name: str,description: str , date: str):
    new_contract = Contract(
        owner_create_id=owner_create_id,
        name = name,
        description = description,
        date = date,)
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract

# task
def create_task(db: Session,owner_id: int,contract_id:int, task_name: str, type:str , deadline : str ):
    new_task = Task(
        owner_id= owner_id,
        contract_id= contract_id,
        task_name= task_name,
        type = type,
        deadline=deadline,)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_all_contract(db: Session, owner_create_id: int, skip: int = 0, limit: int = 10) :
    try:
        return db.query(Contract).filter(Contract.owner_create_id == owner_create_id).offset(skip).limit(limit).all()
    except Exception as e:
        raise Exception(f"An error occurred while fetching contracts: {e}")


# accept
def create_accept(db: Session, user_id: int, contract_id: int):
    try:
        # Check if the assignment already exists
        existing = db.query(AssingCt).filter(
            AssingCt.user_id == user_id, AssingCt.contract_id == contract_id
        ).first()
        if existing:
            raise ValueError("Assignment already exists for this user and contract.")

        # Create the new assignment
        new_accept = AssingCt(user_id=user_id, contract_id=contract_id)
        db.add(new_accept)
        db.commit()
        db.refresh(new_accept)
        return new_accept

    except Exception as e:
        db.rollback()  # Ensure transaction is rolled back
        raise Exception(f"An error occurred while creating accept: {e}")

# 0000
def get_all_ct_acp_with_details(db: Session, user_id: int):
    try:
        return (
            db.query(AssingCt, Contract)
            .join(Contract, AssingCt.contract_id == Contract.contract_id)
            .filter(AssingCt.user_id == user_id)
            .all()
        )
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching accepted contracts: {e}")

def get_number_of_acp_custmer(db: Session, contract_id: int) -> int:
    try:
        return db.query(AssingCt).filter(AssingCt.contract_id == contract_id).count()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching accepted contracts: {e}")




def check_accept_task(
    db: Session,
    current_user_id: int,
    task_id: int,
    contract_id: int
) -> bool:
    try:
        # Check if the task exists and does not belong to the current user
        task = (
            db.query(Task)
            .filter(
                Task.contract_id == contract_id,
                Task.task_id == task_id,
                Task.owner_id != current_user_id
            )
            .one_or_none()
        )
        if not task:
            return False

        # Check if the user is assigned to the contract
        assingct = (
            db.query(AssingCt)
            .filter(
                AssingCt.user_id == current_user_id,
                AssingCt.contract_id == contract_id
            )
            .one_or_none()
        )
        return assingct is not None

    except Exception as e:
        raise Exception(f"An error occurred while checking the task: {e}")

def update_notification_status(
    db: Session,
    notification_id: int,
    notification_status: bool
):
    try:
        # Fetch the notification first to ensure it exists
        notification = db.query(Notification).filter(Notification.notification_id == notification_id).first()
        if not notification:
            raise Exception(f"Notification with ID {notification_id} not found")

        # Update the status
        notification.status = notification_status
        db.commit()

        # Refresh and return the updated notification
        db.refresh(notification)
        return notification

    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while updating notification status: {e}")


def accept_task(
    db: Session,
    accepted_user_id: int,
    task_id: int,
    task_user_status: bool
):
    try:
        # Check accept_task found
        existing_entry = (
            db.query(ActionTask)
            .filter(
                ActionTask.user_id == accepted_user_id,
                ActionTask.task_id == task_id
            )
            .one_or_none()
        )
        if not existing_entry:
            raise Exception("Task accept_task not found ")

        # Update the task_user_status
        existing_entry.task_user_status = task_user_status
        db.commit()
        db.refresh(existing_entry)

        return existing_entry

    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while creating the new_accept_task: {e}")


def accept_task_create(
    db: Session,
    accepted_user_id: int,
    task_id: int,
    task_user_status: bool
):
    try:
        # Check for duplicate entries
        existing_entry = (
            db.query(ActionTask)
            .filter(
                ActionTask.user_id == accepted_user_id,
                ActionTask.task_id == task_id
            )
            .one_or_none()
        )
        if existing_entry:
            raise Exception("Task has already been accepted.")

        # Create a new ActionTask
        new_accept_task = ActionTask(
            user_id=accepted_user_id,
            task_id=task_id,
            task_user_status=task_user_status
        )
        db.add(new_accept_task)
        db.commit()
        db.refresh(new_accept_task)
        return new_accept_task

    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while creating the new_accept_task: {e}")

def create_notification(
    db: Session,
    owner_user_id: int,
    accepted_user_id: int | None,
    contract_id: int,
    task_id: int,
    status: bool,
    description: str
):
    try:
        new_notification = Notification(
            user_id=owner_user_id,
            accepted_user_id=accepted_user_id,
            contract_id=contract_id,
            task_id=task_id,
            status=status,
            description=description
        )
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)
        return new_notification
    except Exception as e:
        db.rollback()
        raise Exception(
            f"An error occurred while creating the notification for contract {contract_id}, task {task_id}: {e}"
        )

def get_notifications_by_user_id(db: Session, user_id: int):
    try:
        return db.query(Notification).filter(Notification.user_id == user_id).all()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching notifications: {e}")


def get_notification_by_id(db: Session, notification_id: int):
    try:
        return db.query(Notification).filter(Notification.notification_id == notification_id).first()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching notification: {e}")


def create_actiontask_accept(db:Session, user_id:int,task_id:int,task_user_status:bool):
    try:
        # Check for duplicate entries
        existing_entry = (
            db.query(ActionTask)
            .filter(
                ActionTask.user_id == user_id,
                ActionTask.task_id == task_id
            )
            .one_or_none()
        )
        if existing_entry:
            raise Exception("Task has already been accepted.")

        new_actiontask = ActionTask(
            user_id = user_id,
            task_id = task_id,
            task_user_status = task_user_status
        )
        db.add(new_actiontask)
        db.commit()
        db.refresh(new_actiontask)
        return new_actiontask
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while creating actiontask: {e}")



def get_assingct_user_id(db: Session, user_id: int, contract_id: int):
    try:
        return db.query(AssingCt).filter(AssingCt.user_id == user_id, AssingCt.contract_id == contract_id).first()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching assingct: {e}")

def get_actiontask_by_user_id_task_id(db: Session, user_id: int,task_id: int):
    try:
        return db.query(ActionTask).filter(ActionTask.user_id == user_id,ActionTask.task_id==task_id).first()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching actiontask: {e}")

def get_assind_users_by_contract_id(db: Session, contract_id: int):
    try:
        return db.query(AssingCt).filter(AssingCt.contract_id == contract_id).all()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching assingct: {e}")

def get_assind_users_by_user_id(db: Session, user_id: int):
    try:
        return db.query(AssingCt).filter(AssingCt.user_id == user_id).all()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching assigned contracts: {e}")


def get_actiontasks_by_user_id(db: Session, user_id: int):
    try:
        return db.query(ActionTask).filter(ActionTask.user_id == user_id).all()
    except Exception as e:
        db.rollback()
        raise Exception(f"An error occurred while fetching actiontask: {e}")
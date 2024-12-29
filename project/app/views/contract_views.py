from fastapi import APIRouter, Depends, HTTPException, Form,status
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError

from typing import List

from project.app.schemas import schemas
from project.app.crud import crud
from project.dependencies import get_db
from project.app.utils import utils as auth_utils
from sqlalchemy.exc import SQLAlchemyError

from fastapi.security import (
    # HTTPBearer,
    # HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="jwt/login/",
)

router = APIRouter(prefix='/contract', tags=["Contract"])

def get_current_token_payload(
    # credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    token: str = Depends(oauth2_scheme),
) -> dict:
    # token = credentials.credentials
    try:
        payload = auth_utils.decode_jwt(
            token=token,
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
            # detail=f"invalid token error",
        )
    return payload

def get_current_auth_user(
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
) -> schemas.UserBase:
    user_name: str | None = payload.get("sub")
    if user := crud.get_user_by_name(db=db, user_name=user_name):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )

def get_current_active_auth_user(
    user: schemas.UserBase = Depends(get_current_auth_user),
):
    if user.active:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="user inactive",
    )

# contract
def validate_and_get_ct(
    name: str = Form(),
    date: str = Form(),
) -> schemas.ContractBase:

    ct = schemas.ContractBase(name=name, date=date)

    return ct
# Notification
def create_rejection_or_acceptance_notification(db, notification, action):
    description = (
        f"Task{notification.task_id} has been {action} by {notification.user_id}"
    )
    return crud.create_notification(
        db=db,
        owner_user_id=notification.accepted_user_id,
        accepted_user_id=None,
        contract_id=notification.contract_id,
        task_id=notification.task_id,
        status=False,
        description=description,
    )


@router.post("/offer", response_model=dict)
async def offer_contart(
    contract: schemas.PostCTWT,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:



        # Create the contract
        new_contract = crud.create_contract(
            db=db,
            owner_create_id=user.id,
            name=contract.name_ct,
            description=contract.description,
            date=contract.date,
        )

        # Create tasks for the contract
        for t in contract.task:
            crud.create_task(
                db=db,
                owner_id=user.id,
                contract_id=new_contract.contract_id,
                task_name=t.task_name,
                type=t.type,
                deadline=t.deadline,
            )


        return {"message": f"Successful add {new_contract.name}"}

    except Exception as e:
        # Roll back the transaction explicitly if something goes wrong
        print(f"Error occurred: {e}")  # Optional logging
        raise HTTPException(status_code=400, detail="Failed to add contract")



@router.post("/accept")
async def accept_contract(
    accept: schemas.Assingct,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Validate contract existence
        ct = crud.get_contract_by_id(db=db, contract_id=accept.contract_id)
        if not ct:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check if the user is not own the contract
        if user.id == ct.owner_create_id :
            raise HTTPException(status_code=404, detail="You can not accept your contract")


        # Create contract acceptance
        asingct = crud.create_accept(db=db, user_id=user.id, contract_id=accept.contract_id)

        # Ensure contract tasks exist
        if not ct.tasks:
            raise HTTPException(status_code=404, detail=f"No tasks found for contract {ct.name}.")

        # Create tasks for the contract
        for task in ct.tasks:
            crud.create_actiontask_accept(
                db=db, user_id=user.id, task_id=task.task_id, task_user_status=False
            )

        # Construct response
        response = {
            "message": f"Successfully accepted contract {ct.name}",
            "contract_id": asingct.contract_id,
            "tasks": [{"task_id": task.task_id, "status": "Pending"} for task in ct.tasks],
        }
        return response

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/accepted_ct_user_id", response_model=List[schemas.AcceptedContract])
async def accepted_ct(
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Fetch accepted contracts with details
        accepted = crud.get_all_ct_acp_with_details(db=db, user_id=user.id)

        if not accepted:
            raise HTTPException(status_code=404, detail="No accepted contracts found")

        # Prepare the response
        response = [
            schemas.AcceptedContract(
                contract_id=contract.contract_id,
                owner_create_id=contract.owner_create_id,
                name=contract.name,
                description=contract.description,
                date=contract.date
            )
            for _, contract in accepted
        ]

        return response

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")





@router.get("/all_contract_owner_id", response_model=List[schemas.Contract], status_code=200)
async def all_contracts_of_owner(
    res: schemas.GetAllCt = Depends(),
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):

    try:
        response = crud.get_all_contract(db=db, owner_create_id=user.id, skip=res.skip, limit=res.limit)
        # if not response:
        #     raise HTTPException(status_code=404, detail="No contracts found")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")
    return response


@router.get("/task_contract", response_model=schemas.PostCtwT)
async def taskIdCt(
    contract_id: schemas.CTID,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Fetch the contract
        ct = crud.get_contract_by_id(db=db, contract_id=contract_id.contract_id)
        if not ct:
            raise HTTPException(status_code=404, detail="No contracts found")

        # # Check ownership
        # if user.id != ct.owner_create_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"User does not own the contract {ct.name}",
        #     )



        # Fetch tasks for the contract
        tasks = crud.get_tasks_by_ct_id(db=db, contract_id=ct.contract_id)

        # Get the number of accepted customers
        num_of_ct_assepted_people = crud.get_number_of_acp_custmer(
            db=db, contract_id=contract_id.contract_id
        )

        print("test")
        print(num_of_ct_assepted_people)
        # Set status
        st = num_of_ct_assepted_people > 0



        # Build the response
        response = schemas.PostCtwT(
            statuss=st,
            num_of_ct_assepted_people=num_of_ct_assepted_people,
            name_ct=ct.name,
            task=tasks,
            description=ct.description,
            date=ct.date,
        )
        return response

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/shop")
async def allCT(
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        response = crud.get_all_contracts_except_assigned_and_user(db=db,user_id=user.id)
        if not response:
            raise HTTPException(status_code=404, detail="No contracts found")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")
    return response

@router.post("/accept_task")
async def accept_task(
    atu: schemas.AcceptTaskPost,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Validate if the task can be accepted
        if not crud.check_accept_task(
            db=db,
            current_user_id=user.id,
            task_id=atu.task_id,
            contract_id=atu.contract_id
        ):
            raise HTTPException(status_code=404, detail="Task cannot be accepted.")

        owner_create_id = crud.get_contract_by_id(db=db, contract_id=atu.contract_id).owner_create_id

        # Handle task acceptance and notification creation
        if atu.task_user_status:
            # Create the notification
            nt = crud.create_notification(
                db=db,
                owner_user_id=owner_create_id,
                accepted_user_id=user.id,
                contract_id=atu.contract_id,
                task_id=atu.task_id,
                status=True,
                description = f"this {user.user_name}({user.id}) want coplate the task:{atu.task_id} in contract:{atu.contract_id}",
            )
            return {
                "message": "Notification successfully created.",
                "notification_id": nt.notification_id
            }

        return {"message": "Task was not marked as completed by the user."}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/notification",response_model=List[schemas.GetToResponseNotification])
async def get_notification(
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        notifications_user_id  = crud.get_notifications_by_user_id(db=db, user_id=user.id)

        response = [
            schemas.GetToResponseNotification(
                notification_id=notification.notification_id,
                status=notification.status,
                description=notification.description,
                created_at=notification.created_at,
            )
            for notification in notifications_user_id
        ]

        if not response:
            raise HTTPException(status_code=404, detail="No notifications found")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")
    return response

@router.post("/notification/action")
async def action_notification(
    nt: schemas.PostNotificationAction,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        if nt.status not in [True, False]:
            raise HTTPException(status_code=400, detail="Invalid status value")

        # Validate notification existence
        notification = crud.get_notification_by_id(db=db, notification_id=nt.notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Check ownership
        if notification.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not own the notification",
            )



        # Handle notification action
        action = "accepted" if nt.status else "rejected"
        if nt.status:
            # Accept task

            accept_task = crud.accept_task(
                db=db,
                accepted_user_id=notification.accepted_user_id,
                task_id=notification.task_id,
                task_user_status=True,
            )

            print("test")
            # notfication status false
            crud.update_notification_status(db=db,notification_id=nt.notification_id,notification_status=False)



            if not accept_task:
                raise HTTPException(status_code=500, detail="Failed to accept task up date status")

        # Create notification for the action
        new_notification = create_rejection_or_acceptance_notification(db, notification, action)

        return {"message": f"Notification {action} successfully.", "notification": new_notification}

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unexpected error: {str(e)}")


@router.get("/task_contract_accepted_ct_user_id",response_model=schemas.GetCtaTResponse)
async def task_contract_accepted_ct_user_id(
    ct_id: schemas.CTID,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Validate contract existence
        ct = crud.get_contract_by_id(db=db, contract_id=ct_id.contract_id)
        if not ct:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check if user is assigned to the contract
        check = crud.get_assingct_user_id(db=db, user_id=user.id, contract_id=ct_id.contract_id)
        if not check:
            raise HTTPException(status_code=404, detail="User not assigned to the contract")

        # Fetch all tasks for the contract
        tasks = crud.get_tasks_by_ct_id(db=db, contract_id=ct_id.contract_id)
        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found for the contract")

        # Build the response using the `get_actiontask_by_user_id_task_id` function
        response = schemas.GetCtaTResponse(
            contract_id=ct.contract_id,
            name=ct.name,
            description=ct.description,
            date=ct.date,
            task=[
                schemas.TaskWithStatus(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    type=task.type,
                    deadline=task.deadline,
                    task_user_status=(
                        crud.get_actiontask_by_user_id_task_id(
                            db=db, user_id=user.id, task_id=task.task_id
                        ).task_user_status
                        if crud.get_actiontask_by_user_id_task_id(
                            db=db, user_id=user.id, task_id=task.task_id
                        )
                        else False
                    ),
                )
                for task in tasks
            ],
        )

        return response

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/task_contract_owner_id", response_model=schemas.GetCtaTResponseOwn)
async def task_contract_owner_id(
    ct_id: schemas.CTID,
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Validate contract existence
        ct = crud.get_contract_by_id(db=db, contract_id=ct_id.contract_id)
        if not ct:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check ownership
        if user.id != ct.owner_create_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not own the contract {ct.name}.",
            )

        # Fetch all tasks for the contract
        tasks = crud.get_tasks_by_ct_id(db=db, contract_id=ct_id.contract_id)
        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found for the contract")

        # Fetch assigned users for the contract
        assigned_users = crud.get_assind_users_by_contract_id(db=db, contract_id=ct_id.contract_id)

        # Build the response
        response = schemas.GetCtaTResponseOwn(
            contract_id=ct.contract_id,
            name=ct.name,
            description=ct.description,
            date=ct.date,
            task=[
                schemas.TaskWithStatusOwn(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    type=task.type,
                    deadline=task.deadline,
                    users_status=[
                        schemas.Users_status(
                            user_id=assigned_user.user_id,
                            status=(
                                action_task.task_user_status
                                if (action_task := crud.get_actiontask_by_user_id_task_id(
                                    db=db, user_id=assigned_user.user_id, task_id=task.task_id
                                ))
                                else False
                            ),
                        )
                        for assigned_user in assigned_users
                    ] if assigned_users else [],
                )
                for task in tasks
            ],
        )

        return response

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")

# show users tasks
@router.get("/tasks_user", response_model=List[schemas.GetTasksUser])
async def get_tasks_for_user(
    user: schemas.User = Depends(get_current_active_auth_user),
    db: Session = Depends(get_db),
):
    try:
        # Fetch all contracts where the user is assigned
        assigned_contracts = crud.get_assind_users_by_user_id(db=db, user_id=user.id)
        if not assigned_contracts:
            return []  # No contracts found for the user

        # Initialize response list
        tasks_user = []

        for assigned_contract in assigned_contracts:
            # Fetch the contract by ID
            contract = crud.get_contract_by_id(db=db, contract_id=assigned_contract.contract_id)
            if not contract:
                continue  # Skip if the contract doesn't exist

            # Fetch tasks for the contract
            tasks = crud.get_tasks_by_ct_id(db=db, contract_id=assigned_contract.contract_id)
            if not tasks:
                continue  # Skip if there are no tasks for the contract

            for task in tasks:
                # Get the user's action task status
                action_task = crud.get_actiontask_by_user_id_task_id(db=db, user_id=user.id, task_id=task.task_id)
                task_status = action_task.task_user_status if action_task else False

                # Add task details to the response
                tasks_user.append(
                    schemas.GetTasksUser(
                        task_id=task.task_id,
                        contract_id=contract.contract_id,
                        contract_name=contract.name,
                        task_name=task.task_name,
                        type=task.type,
                        task_user_status=task_status,
                    )
                )

        return tasks_user

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {str(e)}")





# test
# @router.post("/ofer",response_model=dict)
# def offer(
#         db: Session = Depends(get_db)
# ):
#
#     return {'message':'test'}

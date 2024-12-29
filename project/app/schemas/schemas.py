from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from typing import List


# User
class UserBase(BaseModel):
    id : int | None = None
    user_name: str
    name: str
    phone_number: str | None = None
    email: str | None = None
    password: str
    active: bool = True

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class SignInSchema(BaseModel):
    user_name: str
    user_password: str

# class User


# Token
class TokenInfo(BaseModel):
    access_token: str
    token_type: str


#  contract
class ContractBase(BaseModel):
    name : str

    date : str

class Contract(ContractBase):
    contract_id : int
    owner_create_id : int
    description : str
    created_at: datetime
    updated_at: Optional[datetime]


    class Config:
        from_attributes = True


class GetAllCt(BaseModel):
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of items to retrieve")


# tasks

# Enum for task types
class TaskType(str, Enum):
    act = "act"
    pay = "pay"

class Task(BaseModel):
    task_id: int
    owner_id: int
    contract_id: int
    task_name: str
    type: TaskType
    deadline: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True



#  get ct with task
class TaskCreate(BaseModel):
    task_name : str
    type : TaskType
    deadline : str

class PostCTWT(BaseModel):
    name_ct: str
    description: str
    date: str
    task: List[TaskCreate]

    class Config:
        from_attributes = True

class PostCtwT(BaseModel):
    statuss: bool = False
    num_of_ct_assepted_people: int = 0
    name_ct: str
    description: str
    date: str
    task: List[Task]

    class Config:
        from_attributes = True

class TaskWithStatus(BaseModel):
    task_id: int
    task_name: str
    type: TaskType
    deadline: str
    task_user_status: bool

    class Config:
        from_attributes = True

class GetCtaTResponse(BaseModel):
    contract_id: int
    name: str
    description: str
    date: str
    task: List[TaskWithStatus]

    class Config:
        from_attributes = True

class OfferContractResponse:
    message: str

class Signin(BaseModel):
    user_name: str
    password: str

    class Config:
        from_attributes = True

class CTID(BaseModel):
    contract_id: int

    class Config:
        from_attributes = True


class Assingct(BaseModel):
    contract_id: int = Field(..., gt=0, description="ID of the contract")

    class Config:
        from_attributes = True


class AcceptedContract(BaseModel):
    owner_create_id: int
    contract_id: int
    name: str
    description: str
    date: str

    class Config:
        from_attributes = True


class AcceptTaskPost(BaseModel):
    task_id: int
    contract_id: int
    task_user_status: bool = False

class GetToResponseNotification(BaseModel):
    notification_id: int
    status: bool
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

class PostNotificationAction(BaseModel):
    notification_id: int
    status: bool

    class Config:
        from_attributes = True

class Users_status(BaseModel):
    user_id: int
    status: bool

    class Config:
        from_attributes = True

class TaskWithStatusOwn(BaseModel):
    task_id: int
    task_name: str
    type: TaskType
    deadline: str
    users_status: List[Users_status]

    class Config:
        from_attributes = True

class GetCtaTResponseOwn(BaseModel):
    contract_id: int
    name: str
    description: str
    date: str
    task: List[TaskWithStatusOwn]

    class Config:
        from_attributes = True

class GetTasksUser(BaseModel):
    contract_name: str
    task_name: str
    type: TaskType
    task_user_status: bool

    class Config:
        from_attributes = True
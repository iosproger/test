from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from ..schemas.schemas import TaskType

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contracts = relationship("Contract", back_populates="user")
    assingcts = relationship("AssingCt", back_populates="user")
    actiontasks = relationship("ActionTask", back_populates="user")
    notifications_sent = relationship("Notification", back_populates="user", foreign_keys="[Notification.user_id]")
    notifications_received = relationship("Notification", back_populates="accepted_user",foreign_keys="[Notification.accepted_user_id]")


class Contract(Base):
    __tablename__ = "contract"
    contract_id = Column(Integer, primary_key=True, index=True)
    owner_create_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=False)
    date = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tasks = relationship("Task", back_populates="contract")
    user = relationship("User", back_populates="contracts")
    assingcts = relationship("AssingCt", back_populates="contract")
    notifications = relationship("Notification", back_populates="contract")


class Task(Base):
    __tablename__ = "task"
    task_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    contract_id = Column(Integer, ForeignKey("contract.contract_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    task_name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    deadline = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    contract = relationship("Contract", back_populates="tasks")
    actiontasks = relationship("ActionTask", back_populates="task")
    notifications = relationship("Notification", back_populates="task")

    @validates("type")
    def validate_type(self, key, value):
        if value not in TaskType._value2member_map_:
            raise ValueError(f"Invalid task type: {value}")
        return value


class AssingCt(Base):
    __tablename__ = "assingct"
    assingct_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contract.contract_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # Relationships
    contract = relationship("Contract", back_populates="assingcts")
    user = relationship("User", back_populates="assingcts")


class ActionTask(Base):
    __tablename__ = "actiontask"
    actiontask_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("task.task_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    task_user_status = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="actiontasks")
    task = relationship("Task", back_populates="actiontasks")

class Notification(Base):
    __tablename__ = "notification"
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    accepted_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    contract_id = Column(Integer, ForeignKey("contract.contract_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("task.task_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    status = Column(Boolean, default=False, nullable=False)
    description = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    # Relationships
    user = relationship("User", back_populates="notifications_sent", foreign_keys=[user_id])
    accepted_user = relationship("User", back_populates="notifications_received", foreign_keys=[accepted_user_id])
    contract = relationship("Contract", back_populates="notifications")
    task = relationship("Task", back_populates="notifications")

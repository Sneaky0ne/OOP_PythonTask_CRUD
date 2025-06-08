from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime

app = FastAPI(title="OOP TODO CRUD API")

# Спраочники (хешмпаки) как БД
user_DB: Dict[UUID, 'User'] = {}
project_DB: Dict[UUID, 'Project'] = {}
task_DB: Dict[UUID, 'Task'] = {}



# --------- User классы ---------
class UserCreateDTO(BaseModel):
    username: str
    email: str

class User(UserCreateDTO):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)

class UserResponseDTO(User):
    projects_count: int = 0
    tasks_count: int = 0

    class Config:
        from_attributes = True

# --------- User классы ---------



# --------- Task классы ---------
class TaskCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: UUID
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None

class Task(TaskCreateDTO):
    id: UUID = Field(default_factory=uuid4)
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class TaskUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None

class TaskResponseDTO(Task):
    project_name: Optional[str] = None
    assignee_username: Optional[str] = None
    days_until_due: Optional[int] = None

    class Config:
        from_attributes = True

# --------- Task классы ---------



# --------- Project классы ---------

class ProjectCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: UUID

class Project(ProjectCreateDTO):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)

class ProjectResponseDTO(Project):
    owner_username: Optional[str] = None
    tasks_count: int = 0
    completed_tasks_count: int = 0

    class Config:
        from_attributes = True

# --------- Project классы ---------



# Репозитории
# --------- UserRepository ---------
class UserRepository:

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        for user in user_DB.values():
            if user.username == username:
                return user
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        for user in user_DB.values():
            if user.email == email:
                return user
        return None

    @staticmethod
    def get_all() -> List[User]:
        return list(user_DB.values())
    
    @staticmethod
    def get_by_id(user_id: UUID) -> Optional[User]:
        return user_DB.get(user_id)
    
    @staticmethod
    def create(user: User) -> User:
        user_DB[user.id] = user
        return user
    
    @staticmethod
    def delete(user_id: UUID) -> bool:
        if user_id in user_DB:
            del user_DB[user_id]
            return True
        return False
    
# --------- UserRepository ---------



# --------- ProjectRepository ---------
class ProjectRepository:
    @staticmethod
    def get_all() -> List[Project]:
        return list(project_DB.values())
    
    @staticmethod
    def get_by_id(project_id: UUID) -> Optional[Project]:
        return project_DB.get(project_id)
    
    @staticmethod
    def create(project: Project) -> Project:
        if project.owner_id not in user_DB:
            raise ValueError("Owner does not exist")
        project_DB[project.id] = project
        return project
    
    @staticmethod
    def delete(project_id: UUID) -> bool:
        if project_id in project_DB:
            del project_DB[project_id]
            return True
        return False
    
# --------- ProjectRepository ---------



# --------- TaskRepository ---------
class TaskRepository:
    @staticmethod
    def get_all() -> List[Task]:
        return list(task_DB.values())
    
    @staticmethod
    def get_by_id(task_id: UUID) -> Optional[Task]:
        return task_DB.get(task_id)
    
    @staticmethod
    def create(task: Task) -> Task:
        if task.project_id not in project_DB:
            raise ValueError("Project does not exist")
        if task.assignee_id and task.assignee_id not in user_DB:
            raise ValueError("Assignee does not exist")
        task_DB[task.id] = task
        return task
    
    @staticmethod
    def update(task_id: UUID, task_data: dict) -> Optional[Task]:
        if task_id not in task_DB:
            return None
        
        task = task_DB[task_id]
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task
    
    @staticmethod
    def delete(task_id: UUID) -> bool:
        if task_id in task_DB:
            del task_DB[task_id]
            return True
        return False
    
# --------- TaskRepository ---------



# ------------

# Хелперы / ютилки, чтобы было не так скучно отправлять данные обратно

def enrich_user_data(user: User) -> UserResponseDTO:
    projects_count = sum(1 for p in project_DB.values() if p.owner_id == user.id)
    tasks_count = sum(1 for t in task_DB.values() if t.assignee_id == user.id)
    
    return UserResponseDTO(
        **user.model_dump(),
        projects_count=projects_count,
        tasks_count=tasks_count
    )

def enrich_project_data(project: Project) -> ProjectResponseDTO:
    owner = user_DB.get(project.owner_id)
    project_tasks = [t for t in task_DB.values() if t.project_id == project.id]
    
    return ProjectResponseDTO(
        **project.model_dump(),
        owner_username=owner.username if owner else None,
        tasks_count=len(project_tasks),
        completed_tasks_count=sum(1 for t in project_tasks if t.completed)
    )

def enrich_task_data(task: Task) -> TaskResponseDTO:
    project = project_DB.get(task.project_id)
    assignee = user_DB.get(task.assignee_id) if task.assignee_id else None
    
    days_until_due = None
    if task.due_date:
        delta = task.due_date - datetime.now()
        days_until_due = delta.days
    
    return TaskResponseDTO(
        **task.model_dump(),
        project_name=project.name if project else None,
        assignee_username=assignee.username if assignee else None,
        days_until_due=days_until_due
    )

# ------------



# --------- User API ---------
@app.get("/users", response_model=List[UserResponseDTO])
def get_all_users():
    return [enrich_user_data(u) for u in UserRepository.get_all()]

@app.post("/users", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreateDTO):

    # Валидация, проверяем, существует ли пользователь с таким username
    if UserRepository.get_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Проверяем, существует ли пользователь с таким email
    if UserRepository.get_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    user = User(**user_data.model_dump())
    created_user = UserRepository.create(user)
    return enrich_user_data(created_user)

@app.get("/users/{user_id}", response_model=UserResponseDTO)
def get_user(user_id: UUID):
    user = UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return enrich_user_data(user)

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID):
    if not UserRepository.delete(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
# --------- User API ---------



# --------- Project API ---------
@app.get("/projects", response_model=List[ProjectResponseDTO])
def get_all_projects():
    return [enrich_project_data(p) for p in ProjectRepository.get_all()]

@app.post("/projects", response_model=ProjectResponseDTO, status_code=status.HTTP_201_CREATED)
def create_project(project_data: ProjectCreateDTO):
    try:
        project = Project(**project_data.model_dump())
        created_project = ProjectRepository.create(project)
        return enrich_project_data(created_project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}", response_model=ProjectResponseDTO)
def get_project(project_id: UUID):
    project = ProjectRepository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return enrich_project_data(project)

@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID):
    if not ProjectRepository.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

@app.get("/projects/{project_id}/tasks", response_model=List[TaskResponseDTO])
def get_project_tasks(project_id: UUID):
    if project_id not in project_DB:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = [t for t in task_DB.values() if t.project_id == project_id]
    return [enrich_task_data(t) for t in tasks]

# --------- Project API ---------



# --------- Task API ---------
@app.get("/tasks", response_model=List[TaskResponseDTO])
def get_all_tasks():
    return [enrich_task_data(t) for t in TaskRepository.get_all()]

@app.post("/tasks", response_model=TaskResponseDTO, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreateDTO):
    try:
        task = Task(**task_data.model_dump())
        created_task = TaskRepository.create(task)
        return enrich_task_data(created_task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks/{task_id}", response_model=TaskResponseDTO)
def get_task(task_id: UUID):
    task = TaskRepository.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return enrich_task_data(task)

@app.patch("/tasks/{task_id}", response_model=TaskResponseDTO)
def update_task(task_id: UUID, task_data: TaskUpdateDTO):
    task = TaskRepository.update(task_id, task_data.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return enrich_task_data(task)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    if not TaskRepository.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
# --------- Task API ---------
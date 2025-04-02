from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Task Management API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic data models
class Project(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    priority: int
    status: str = "active"

class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    priority: int
    status: str = "pending"
    project_id: Optional[int] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

# In-memory storage for demo
projects = []
tasks = []

@app.get("/")
async def root():
    return {"message": "Task Management API is running"}

@app.get("/projects", response_model=List[Project])
async def get_projects():
    return projects

@app.post("/projects", response_model=Project)
async def create_project(project: Project):
    project.id = len(projects) + 1
    projects.append(project)
    return project

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    for project in projects:
        if project.id == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")

@app.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: int, project: Project):
    for i, p in enumerate(projects):
        if p.id == project_id:
            project.id = project_id
            projects[i] = project
            return project
    raise HTTPException(status_code=404, detail="Project not found")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    for i, project in enumerate(projects):
        if project.id == project_id:
            # Remove all tasks associated with this project
            global tasks
            tasks = [task for task in tasks if task.project_id != project_id]
            # Remove the project
            projects.pop(i)
            return {"message": f"Project {project_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Project not found")

@app.get("/tasks", response_model=List[Task])
async def get_tasks(project_id: Optional[int] = None, status: Optional[str] = None):
    if project_id is not None:
        return [task for task in tasks if task.project_id == project_id]
    if status is not None:
        return [task for task in tasks if task.status == status]
    return tasks

@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    task.id = len(tasks) + 1
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: Task):
    for i, t in enumerate(tasks):
        if t.id == task_id:
            task.id = task_id
            tasks[i] = task
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(i)
            return {"message": f"Task {task_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/tasks/{task_id}/comments", response_model=List[dict])
async def get_task_comments(task_id: int):
    # In a real app, this would fetch from a database
    return []

@app.post("/tasks/{task_id}/comments")
async def add_task_comment(task_id: int, comment: dict):
    # In a real app, this would save to a database
    return comment

@app.get("/analytics/project-progress/{project_id}")
async def get_project_progress(project_id: int):
    project_tasks = [task for task in tasks if task.project_id == project_id]
    total_tasks = len(project_tasks)
    completed_tasks = len([task for task in project_tasks if task.status == "completed"])
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    return {
        "progress": progress,
        "completed": completed_tasks,
        "total": total_tasks
    }

@app.get("/analytics/workflow-metrics")
async def get_workflow_metrics():
    return {
        "total_tasks": len(tasks),
        "completed_tasks": len([t for t in tasks if t.status == "completed"]),
        "pending_tasks": len([t for t in tasks if t.status == "pending"]),
        "in_progress_tasks": len([t for t in tasks if t.status == "in_progress"])
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
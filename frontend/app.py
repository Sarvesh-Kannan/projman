import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np

# Configure the page
st.set_page_config(
    page_title="Project Management Dashboard",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .task-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .project-card {
        background-color: #e6f7ff;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    </style>
""", unsafe_allow_html=True)

# API endpoint
API_URL = "http://localhost:8000"

# Helper functions
def fetch_projects():
    try:
        response = requests.get(f"{API_URL}/projects")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def fetch_tasks(project_id=None, status=None):
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        
        response = requests.get(f"{API_URL}/tasks", params=params)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def fetch_task_metrics(task_id):
    try:
        response = requests.get(f"{API_URL}/analytics/task-metrics/{task_id}")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def fetch_project_progress(project_id):
    try:
        response = requests.get(f"{API_URL}/analytics/project-progress/{project_id}")
        return response.json() if response.status_code == 200 else {"progress": 0, "completed": 0, "total": 0}
    except:
        return {"progress": 0, "completed": 0, "total": 0}

def fetch_workflow_metrics():
    try:
        response = requests.get(f"{API_URL}/analytics/workflow-metrics")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def create_project(name, description, priority):
    try:
        project_data = {
            "name": name,
            "description": description,
            "priority": priority,
            "status": "active"
        }
        response = requests.post(f"{API_URL}/projects", json=project_data)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def create_task(title, description, priority, project_id=None, assigned_to=None, due_date=None):
    try:
        task_data = {
            "title": title,
            "description": description,
            "priority": priority,
            "project_id": project_id,
            "assigned_to": assigned_to,
            "due_date": due_date.isoformat() if due_date else None
        }
        response = requests.post(f"{API_URL}/tasks", json=task_data)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def update_task(task_id, update_data):
    response = requests.put(f"{API_URL}/tasks/{task_id}", json=update_data)
    return response.json()

def add_task_dependency(task_id, depends_on_id):
    dependency_data = {
        "depends_on_id": depends_on_id,
        "dependency_type": "finish_to_start"
    }
    response = requests.post(f"{API_URL}/tasks/{task_id}/dependencies", json=dependency_data)
    return response.json()

def add_task_comment(task_id, content, author):
    comment_data = {
        "content": content,
        "author": author
    }
    response = requests.post(f"{API_URL}/tasks/{task_id}/comments", json=comment_data)
    return response.json()

# Sidebar navigation
st.sidebar.title("Project Management")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Projects", "Tasks", "Dependencies", "Analytics", "Settings"]
)

# Dashboard page
if page == "Dashboard":
    st.title("📊 Project Management Dashboard")
    
    # Fetch data
    projects = fetch_projects()
    tasks = fetch_tasks()
    workflow_metrics = fetch_workflow_metrics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_projects = len([p for p in projects if isinstance(p, dict) and p.get("status") == "active"])
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{active_projects}</div>
                <div class="metric-label">Active Projects</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pending_tasks = len([t for t in tasks if isinstance(t, dict) and t.get("status") == "pending"])
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{pending_tasks}</div>
                <div class="metric-label">Pending Tasks</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        in_progress_tasks = len([t for t in tasks if isinstance(t, dict) and t.get("status") == "in_progress"])
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{in_progress_tasks}</div>
                <div class="metric-label">In Progress Tasks</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        completed_tasks = len([t for t in tasks if isinstance(t, dict) and t.get("status") == "completed"])
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{completed_tasks}</div>
                <div class="metric-label">Completed Tasks</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Project progress
    st.subheader("Project Progress")
    
    if projects:
        project_data = []
        for project in projects:
            if isinstance(project, dict):
                progress = fetch_project_progress(project.get("id"))
                project_data.append({
                    "Project": project.get("name", "Unknown"),
                    "Progress": progress.get("progress", 0),
                    "Completed": progress.get("completed", 0),
                    "Total": progress.get("total", 0)
                })
        
        if project_data:
            df = pd.DataFrame(project_data)
            
            fig = px.bar(
                df, 
                x="Project", 
                y="Progress",
                color="Progress",
                color_continuous_scale="Greens",
                title="Project Completion Progress"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No project data available.")
    else:
        st.info("No projects found. Create a project to see progress.")
    
    # Task status distribution
    st.subheader("Task Status Distribution")
    
    if tasks:
        status_data = []
        for task in tasks:
            if isinstance(task, dict):
                status_data.append(task.get("status", "unknown"))
        
        if status_data:
            status_counts = pd.DataFrame(status_data, columns=["Status"]).value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig = px.pie(
                status_counts, 
                values="Count", 
                names="Status",
                title="Task Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No task status data available.")
    else:
        st.info("No tasks found. Create tasks to see distribution.")
    
    # Recent workflow metrics
    st.subheader("Recent Workflow Metrics")
    
    if workflow_metrics and isinstance(workflow_metrics, list) and len(workflow_metrics) > 0:
        try:
            metrics_data = {
                "Total Tasks": workflow_metrics[0].get("total_tasks", 0),
                "Completed Tasks": workflow_metrics[0].get("completed_tasks", 0),
                "Pending Tasks": workflow_metrics[0].get("pending_tasks", 0),
                "In Progress Tasks": workflow_metrics[0].get("in_progress_tasks", 0)
            }
            
            metrics_df = pd.DataFrame(list(metrics_data.items()), columns=["Metric", "Value"])
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=metrics_df["Metric"],
                y=metrics_df["Value"],
                marker_color="green"
            ))
            
            fig.update_layout(
                title="Workflow Metrics Overview",
                xaxis_title="Metric",
                yaxis_title="Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error processing workflow metrics: {str(e)}")
    else:
        st.info("No workflow metrics available yet")

# Projects page
elif page == "Projects":
    st.title("📋 Projects")
    
    # Fetch projects
    projects = fetch_projects()
    
    # Create new project
    with st.expander("Create New Project", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name")
            project_description = st.text_area("Project Description")
        with col2:
            project_priority = st.slider("Priority", 1, 5, 3)
            if st.button("Create Project"):
                if project_name and project_description:
                    result = create_project(project_name, project_description, project_priority)
                    if result:
                        st.success("Project created successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create project")
                else:
                    st.error("Please fill in all fields")
    
    # Display projects
    st.subheader("All Projects")
    
    if projects:
        for project in projects:
            if isinstance(project, dict):
                with st.container():
                    st.markdown(f"""
                        <div class="project-card">
                            <h3>{project.get('name', 'Unknown')}</h3>
                            <p>{project.get('description', 'No description')}</p>
                            <p>Priority: {'⭐' * project.get('priority', 1)}</p>
                            <p>Status: {project.get('status', 'unknown')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Project actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"View Tasks ({project.get('id', 'N/A')})"):
                            st.session_state.project_id = project.get('id')
                            st.session_state.page = "Tasks"
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Edit Project ({project.get('id', 'N/A')})"):
                            st.session_state.edit_project = project
                            st.experimental_rerun()
                    with col3:
                        if st.button(f"Delete Project ({project.get('id', 'N/A')})"):
                            st.warning("Project deletion not implemented in this demo")
                    
                    st.markdown("---")
    else:
        st.info("No projects found. Create a project to get started.")

# Tasks page
elif page == "Tasks":
    st.title("✅ Tasks")
    
    # Fetch tasks
    project_id = getattr(st.session_state, 'project_id', None)
    tasks = fetch_tasks(project_id=project_id)
    
    # Create new task
    with st.expander("Create New Task", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task Title")
            task_description = st.text_area("Task Description")
            task_priority = st.slider("Priority", 1, 5, 3)
        with col2:
            # Project selection
            projects = fetch_projects()
            project_options = {p.get("name", "Unknown"): p.get("id") for p in projects if isinstance(p, dict)}
            selected_project = st.selectbox("Project", options=["None"] + list(project_options.keys()))
            
            task_assigned_to = st.text_input("Assigned To")
            task_due_date = st.date_input("Due Date")
            
            if st.button("Create Task"):
                if task_title and task_description:
                    project_id = project_options.get(selected_project) if selected_project != "None" else None
                    result = create_task(
                        task_title,
                        task_description,
                        task_priority,
                        project_id,
                        task_assigned_to,
                        task_due_date
                    )
                    if result:
                        st.success("Task created successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create task")
                else:
                    st.error("Please fill in all required fields")
    
    # Display tasks
    st.subheader("All Tasks")
    
    if tasks:
        for task in tasks:
            if isinstance(task, dict):
                with st.container():
                    st.markdown(f"""
                        <div class="task-card">
                            <h3>{task.get('title', 'Unknown')}</h3>
                            <p>{task.get('description', 'No description')}</p>
                            <p>Priority: {'⭐' * task.get('priority', 1)}</p>
                            <p>Status: {task.get('status', 'unknown')}</p>
                            <p>Assigned to: {task.get('assigned_to', 'Unassigned')}</p>
                            <p>Due date: {task.get('due_date', 'No due date')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Task actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Update Status ({task.get('id', 'N/A')})"):
                            st.session_state.edit_task = task
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Add Comment ({task.get('id', 'N/A')})"):
                            st.session_state.comment_task = task
                            st.experimental_rerun()
                    with col3:
                        if st.button(f"Delete Task ({task.get('id', 'N/A')})"):
                            st.warning("Task deletion not implemented in this demo")
                    
                    st.markdown("---")
    else:
        st.info("No tasks found. Create a task to get started.")

# Dependencies page
elif page == "Dependencies":
    st.title("🔗 Task Dependencies")
    
    # Fetch tasks
    tasks = fetch_tasks()
    
    if tasks and len(tasks) > 1:  # Need at least 2 tasks for dependencies
        # Task selection
        col1, col2 = st.columns(2)
        with col1:
            task_options = {f"{t.get('id', '')} - {t.get('title', 'Unknown')}": t.get('id') for t in tasks if isinstance(t, dict) and t.get('id')}
            if task_options:
                selected_task = st.selectbox("Select Task", options=list(task_options.keys()))
                task_id = task_options.get(selected_task)
            else:
                st.warning("No valid tasks available for selection")
                task_id = None
        
        with col2:
            if task_id:
                dependency_options = {f"{t.get('id', '')} - {t.get('title', 'Unknown')}": t.get('id') 
                                   for t in tasks if isinstance(t, dict) and t.get('id') and t.get('id') != task_id}
                if dependency_options:
                    selected_dependency = st.selectbox("Select Dependency", options=list(dependency_options.keys()))
                    dependency_id = dependency_options.get(selected_dependency)
                else:
                    st.warning("No valid dependencies available for selection")
                    dependency_id = None
            else:
                st.warning("Please select a task first")
                dependency_id = None
        
        if task_id and dependency_id and st.button("Add Dependency"):
            add_task_dependency(task_id, dependency_id)
            st.success(f"Dependency added: Task {task_id} depends on Task {dependency_id}")
        
        # Display dependency graph
        st.subheader("Dependency Graph")
        
        # Create a simple visualization of dependencies
        import networkx as nx
        import matplotlib.pyplot as plt
        
        G = nx.DiGraph()
        
        # Add nodes
        for task in tasks:
            G.add_node(task['id'], title=task['title'])
        
        # Add edges (dependencies)
        for task in tasks:
            try:
                dependencies = requests.get(f"{API_URL}/tasks/{task['id']}/dependencies").json()
                for dep in dependencies:
                    G.add_edge(dep['depends_on_id'], task['id'])
            except:
                pass
        
        # Create the graph visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=1000, font_size=8, font_weight='bold', 
                arrows=True, ax=ax)
        
        st.pyplot(fig)
    else:
        st.info("No tasks found. Create tasks to manage dependencies.")

# Analytics page
elif page == "Analytics":
    st.title("📈 Analytics")
    
    # Fetch data
    projects = fetch_projects()
    tasks = fetch_tasks()
    workflow_metrics = fetch_workflow_metrics()
    
    # Task metrics
    st.subheader("Task Metrics")
    
    if tasks:
        # Convert to DataFrame
        tasks_df = pd.DataFrame(tasks)
        
        # Priority distribution
        fig = px.histogram(
            tasks_df, 
            x="priority",
            title="Task Priority Distribution",
            labels={"priority": "Priority Level", "count": "Number of Tasks"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Status distribution
        fig = px.pie(
            tasks_df, 
            names="status",
            title="Task Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Task completion over time
        if "completed_at" in tasks_df.columns and not tasks_df["completed_at"].isna().all():
            tasks_df["completed_at"] = pd.to_datetime(tasks_df["completed_at"])
            tasks_df["completion_date"] = tasks_df["completed_at"].dt.date
            
            completion_counts = tasks_df.groupby("completion_date").size().reset_index(name="count")
            
            fig = px.line(
                completion_counts,
                x="completion_date",
                y="count",
                title="Task Completions Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Project metrics
    st.subheader("Project Metrics")
    
    if projects:
        # Project progress
        project_progress = []
        for project in projects:
            progress = fetch_project_progress(project["id"])
            project_progress.append({
                "Project": project["name"],
                "Progress": progress["progress"],
                "Completed": progress["completed"],
                "Total": progress["total"]
            })
        
        progress_df = pd.DataFrame(project_progress)
        
        fig = px.bar(
            progress_df,
            x="Project",
            y=["Completed", "Total"],
            title="Project Task Completion",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Workflow metrics
    st.subheader("Workflow Metrics")
    
    if workflow_metrics and isinstance(workflow_metrics, list) and len(workflow_metrics) > 0:
        try:
            metrics_df = pd.DataFrame(workflow_metrics)
            if not metrics_df.empty:
                metrics_df["start_time"] = pd.to_datetime(metrics_df["start_time"])
                metrics_df["end_time"] = pd.to_datetime(metrics_df["end_time"])
                metrics_df["duration"] = (metrics_df["end_time"] - metrics_df["start_time"]).dt.total_seconds() / 60  # in minutes
                
                # Tasks processed over time
                fig = px.line(
                    metrics_df,
                    x="start_time",
                    y="tasks_processed",
                    title="Tasks Processed Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Error rate
                fig = px.line(
                    metrics_df,
                    x="start_time",
                    y="errors",
                    title="Workflow Errors Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Duration vs tasks processed
                fig = px.scatter(
                    metrics_df,
                    x="tasks_processed",
                    y="duration",
                    title="Duration vs Tasks Processed",
                    labels={"duration": "Duration (minutes)", "tasks_processed": "Tasks Processed"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No workflow metrics data available")
        except Exception as e:
            st.error(f"Error processing workflow metrics: {str(e)}")
    else:
        st.info("No workflow metrics available yet")

# Settings page
elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("API Configuration")
    api_url = st.text_input("API URL", value=API_URL)
    
    st.subheader("User Preferences")
    theme = st.selectbox("Theme", options=["Light", "Dark"])
    refresh_rate = st.slider("Dashboard Refresh Rate (seconds)", 5, 60, 30)
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")
        # In a real app, we would save these settings

# Task Details page (accessed from Tasks page)
elif page == "Task Details":
    task_id = getattr(st.session_state, 'task_id', None)
    
    if task_id:
        # Fetch task details
        response = requests.get(f"{API_URL}/tasks/{task_id}")
        task = response.json()
        
        st.title(f"Task Details: {task['title']}")
        
        # Task information
        st.subheader("Task Information")
        st.write(f"**Description:** {task['description']}")
        st.write(f"**Status:** {task['status']}")
        st.write(f"**Priority:** {'⭐' * task['priority']}")
        st.write(f"**Created:** {task['created_at']}")
        if task.get('completed_at'):
            st.write(f"**Completed:** {task['completed_at']}")
        
        # Task metrics
        st.subheader("Task Metrics")
        metrics = fetch_task_metrics(task_id)
        
        if metrics:
            metrics_df = pd.DataFrame(metrics)
            
            # Display metrics
            for _, metric in metrics_df.iterrows():
                st.write(f"**{metric['type']}:** {metric['value']}")
            
            # Visualize metrics
            fig = px.bar(
                metrics_df,
                x="type",
                y="value",
                title="Task Metrics"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No metrics available for this task.")
        
        # Comments
        st.subheader("Comments")
        comments = requests.get(f"{API_URL}/tasks/{task_id}/comments").json()
        
        if comments:
            for comment in comments:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <p><strong>{comment['author']}</strong> - {comment['created_at']}</p>
                        <p>{comment['content']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No comments yet.")
        
        # Add comment
        with st.expander("Add Comment"):
            comment_content = st.text_area("Comment")
            comment_author = st.text_input("Your Name")
            
            if st.button("Submit Comment"):
                if comment_content and comment_author:
                    add_task_comment(task_id, comment_content, comment_author)
                    st.success("Comment added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Please fill in all fields")
        
        # Back button
        if st.button("Back to Tasks"):
            st.session_state.page = "Tasks"
            st.experimental_rerun()
    else:
        st.error("Task ID not found. Please select a task from the Tasks page.")
        if st.button("Go to Tasks"):
            st.session_state.page = "Tasks"
            st.experimental_rerun() 
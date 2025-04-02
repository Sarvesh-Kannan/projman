from prefect import flow, task
from datetime import datetime, timedelta
import requests
import json
from typing import List, Dict, Any, Set
import logging
import networkx as nx
from sqlalchemy.orm import Session
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"

@task(retries=3, retry_delay_seconds=5)
def fetch_pending_tasks() -> List[Dict[str, Any]]:
    """Task: Fetch all pending tasks from the API"""
    try:
        response = requests.get(f"{API_URL}/tasks")
        response.raise_for_status()
        tasks = response.json()
        pending_tasks = [task for task in tasks if task["status"] == "pending"]
        logger.info(f"Found {len(pending_tasks)} pending tasks")
        return pending_tasks
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise

@task(retries=2, retry_delay_seconds=3)
def fetch_task_dependencies(task_id: int) -> List[Dict[str, Any]]:
    """Task: Fetch dependencies for a specific task"""
    try:
        response = requests.get(f"{API_URL}/tasks/{task_id}/dependencies")
        response.raise_for_status()
        dependencies = response.json()
        logger.info(f"Found {len(dependencies)} dependencies for task {task_id}")
        return dependencies
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching dependencies for task {task_id}: {str(e)}")
        return []

@task
def build_dependency_graph(tasks: List[Dict[str, Any]]) -> nx.DiGraph:
    """Task: Build a directed graph of task dependencies"""
    graph = nx.DiGraph()
    
    # Add all tasks as nodes
    for task in tasks:
        graph.add_node(task["id"], task=task)
    
    # Add dependencies as edges
    for task in tasks:
        dependencies = fetch_task_dependencies(task["id"])
        for dep in dependencies:
            graph.add_edge(dep["depends_on_id"], task["id"])
    
    # Check for cycles
    if not nx.is_directed_acyclic_graph(graph):
        cycles = list(nx.simple_cycles(graph))
        logger.warning(f"Found dependency cycles: {cycles}")
        # Remove cycles to make it a DAG
        for cycle in cycles:
            # Remove the last edge in the cycle
            graph.remove_edge(cycle[-2], cycle[-1])
    
    return graph

@task
def get_execution_order(graph: nx.DiGraph) -> List[int]:
    """Task: Determine the order in which tasks should be executed"""
    try:
        # Use topological sort to get execution order
        execution_order = list(nx.topological_sort(graph))
        logger.info(f"Determined execution order: {execution_order}")
        return execution_order
    except nx.NetworkXUnfeasible:
        logger.error("Cannot determine execution order due to cycles in dependency graph")
        # Fall back to a simple ordering by priority and creation date
        nodes = list(graph.nodes(data=True))
        return sorted(nodes, key=lambda x: (-x[1]["task"]["priority"], x[1]["task"]["created_at"]))[:0]

@task(retries=2, retry_delay_seconds=3)
def process_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Task: Process a single task and update its status"""
    try:
        logger.info(f"Processing task: {task['title']}")
        
        # Record start time for metrics
        start_time = time.time()
        
        # Update task status to in_progress
        task["status"] = "in_progress"
        response = requests.put(f"{API_URL}/tasks/{task['id']}", json=task)
        response.raise_for_status()
        
        # Simulate task processing (in a real system, this would be the actual work)
        # For now, we'll just sleep for a short time
        time.sleep(1)
        
        # Record processing time
        processing_time = time.time() - start_time
        
        # Update task with processing metrics
        task["processing_time"] = processing_time
        
        return task
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing task {task['id']}: {str(e)}")
        raise

@task(retries=2, retry_delay_seconds=3)
def complete_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Task: Mark a task as completed"""
    try:
        logger.info(f"Completing task: {task['title']}")
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        response = requests.put(f"{API_URL}/tasks/{task['id']}", json=task)
        response.raise_for_status()
        return task
    except requests.exceptions.RequestException as e:
        logger.error(f"Error completing task {task['id']}: {str(e)}")
        raise

@task
def analyze_task_priority(task: Dict[str, Any]) -> int:
    """Task: Analyze and potentially update task priority"""
    # Simple priority analysis based on description length and keywords
    description = task["description"].lower()
    priority = task["priority"]
    
    # Adjust priority based on keywords
    urgent_keywords = ["urgent", "asap", "critical", "important"]
    if any(keyword in description for keyword in urgent_keywords):
        priority = max(priority, 4)
    
    # Adjust based on description length (longer descriptions might be more complex)
    if len(description.split()) > 50:
        priority = min(priority + 1, 5)
    
    return priority

@task
def record_workflow_metrics(flow_name: str, run_id: str, tasks_processed: int, errors: int):
    """Task: Record workflow execution metrics"""
    try:
        metrics = {
            "flow_name": flow_name,
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "status": "completed",
            "tasks_processed": tasks_processed,
            "errors": errors
        }
        
        response = requests.post(f"{API_URL}/analytics/workflow-metrics", json=metrics)
        response.raise_for_status()
        logger.info(f"Recorded workflow metrics: {metrics}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error recording workflow metrics: {str(e)}")

@task
def check_task_dependencies_ready(task_id: int, completed_tasks: Set[int]) -> bool:
    """Task: Check if all dependencies for a task are completed"""
    try:
        dependencies = fetch_task_dependencies(task_id)
        for dep in dependencies:
            if dep["depends_on_id"] not in completed_tasks:
                logger.info(f"Task {task_id} dependencies not ready yet")
                return False
        
        logger.info(f"All dependencies for task {task_id} are ready")
        return True
    except Exception as e:
        logger.error(f"Error checking dependencies for task {task_id}: {str(e)}")
        return False

@flow(name="Task Processing Flow", log_prints=True)
def task_processing_flow():
    """Flow: Main workflow for processing tasks"""
    logger.info("Starting task processing flow")
    
    # Record flow start time and ID
    flow_start_time = datetime.now()
    flow_run_id = f"flow_{flow_start_time.strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize metrics
    tasks_processed = 0
    errors = 0
    
    try:
        # Fetch all pending tasks
        pending_tasks = fetch_pending_tasks()
        
        if not pending_tasks:
            logger.info("No pending tasks to process")
            record_workflow_metrics("Task Processing Flow", flow_run_id, 0, 0)
            return
        
        # Build dependency graph
        dependency_graph = build_dependency_graph(pending_tasks)
        
        # Get execution order
        execution_order = get_execution_order(dependency_graph)
        
        # Track completed tasks
        completed_tasks = set()
        
        # Process tasks in dependency order
        for task_id in execution_order:
            task_data = dependency_graph.nodes[task_id]["task"]
            
            # Check if dependencies are ready
            if not check_task_dependencies_ready(task_id, completed_tasks):
                logger.info(f"Skipping task {task_id} as dependencies are not ready")
                continue
            
            try:
                # Analyze and update priority if needed
                new_priority = analyze_task_priority(task_data)
                if new_priority != task_data["priority"]:
                    task_data["priority"] = new_priority
                    logger.info(f"Updated priority for task {task_id} to {new_priority}")
                
                # Process the task
                processed_task = process_task(task_data)
                
                # Complete the task
                completed_task = complete_task(processed_task)
                
                # Mark as completed
                completed_tasks.add(task_id)
                tasks_processed += 1
                
                logger.info(f"Successfully completed task: {completed_task['title']}")
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {str(e)}")
                errors += 1
                continue
        
        logger.info("Task processing flow completed")
        
    except Exception as e:
        logger.error(f"Error in task processing flow: {str(e)}")
        errors += 1
    
    finally:
        # Record workflow metrics
        record_workflow_metrics("Task Processing Flow", flow_run_id, tasks_processed, errors)

if __name__ == "__main__":
    task_processing_flow() 
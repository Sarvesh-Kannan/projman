from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from flows.task_scheduler import task_processing_flow

# Create a deployment that runs every 5 minutes
deployment = Deployment.build_from_flow(
    flow=task_processing_flow,
    name="task-processor",
    schedule=CronSchedule(cron="*/5 * * * *"),  # Run every 5 minutes
    work_queue_name="task-processing",
    tags=["tasks", "automation"]
)

if __name__ == "__main__":
    deployment.apply() 
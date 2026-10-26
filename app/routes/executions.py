# this route receice the request, validates the email data, find the workflow and delegates the actual work to execute_workflow

from datetime import datetime

from flask import Blueprint, current_app, request

from app import db
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.services.workflow_engine import execute_workflow

executions_bp = Blueprint("executions", __name__)


@executions_bp.route(
    "/api/workflows/<int:workflow_id>/execute",
    methods=["POST"]
)
def execute_workflow_route(workflow_id):
    email = request.get_json(silent=True)

    if not isinstance(email, dict):
        return {"error": "A JSON object is required."}, 400

    subject = email.get("subject", "")
    body = email.get("body", "")

    if not isinstance(subject, str) or not isinstance(body, str):
        return {"error": "subject and body must be strings."}, 400

    workflow = db.session.get(Workflow, workflow_id)

    if workflow is None:
        return {"error": "Workflow not found."}, 404

    # 1. Create a history record before executing the workflow.
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        input_data={
            "subject": subject,
            "body": body
        },
        status="running"
    )

    try:
        db.session.add(execution)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Could not create workflow execution record."
        )
        return {"error": "Could not start workflow execution."}, 500

    # Save the ID so we can retrieve this record if execution fails.
    execution_id = execution.id

    # 2. Run the workflow engine and save the outcome.
    try:
        result = execute_workflow(
            workflow,
            {
                "subject": subject,
                "body": body
            }
        )

        execution.status = result.get("status", "failed")
        execution.result = result
        execution.finished_at = datetime.utcnow()

        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Workflow execution failed."
        )

        # The initial record was already committed, so retrieve it again.
        execution = db.session.get(
            WorkflowExecution,
            execution_id
        )

        execution.status = "failed"
        execution.result = {
            "error": "An unexpected error occurred during execution."
        }
        execution.finished_at = datetime.utcnow()

        db.session.commit()

        return {
            "workflow_id": workflow.id,
            "execution_id": execution_id,
            "status": "failed",
            "error": "Workflow execution failed."
        }, 500

    # 3. Return the saved execution result.
    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "execution_id": execution.id,
        "result": execution.result
    }, 200

    
@executions_bp.route(
    "/api/workflows/<int:workflow_id>/executions",
    methods=["GET"]
)
def get_workflow_executions(workflow_id):
    # 1. Confirm that the workflow exists.
    workflow = db.session.get(Workflow, workflow_id)

    if workflow is None:
        return {"error": "Workflow not found."}, 404

    # 2. Retrieve the most recent 50 executions.
    executions = WorkflowExecution.query.filter_by(
        workflow_id=workflow_id
    ).order_by(
        WorkflowExecution.started_at.desc()
    ).limit(50).all()

    # 3. Convert the database records into JSON-friendly data.
    execution_history = []

    for execution in executions:
        execution_history.append({
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input_data": execution.input_data,
            "result": execution.result,
            "started_at": (
                execution.started_at.isoformat()
                if execution.started_at else None
            ),
            "finished_at": (
                execution.finished_at.isoformat()
                if execution.finished_at else None
            )
        })

    # 4. Return the history to the client.
    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "count": len(execution_history),
        "executions": execution_history
    }, 200




"""
#old code
from flask import Blueprint, request
from app import db
from app.models.workflow import Workflow
from app.services.workflow_engine import execute_workflow

executions_bp = Blueprint("executions", __name__)


@executions_bp.route(
    "/api/workflows/<int:workflow_id>/execute",
    methods=["POST"]
)
def execute_workflow_route(workflow_id):
    email = request.get_json(silent=True)

    if not isinstance(email, dict):
        return {"error": "A JSON object is required."}, 400

    subject = email.get("subject", "")
    body = email.get("body", "")

    if not isinstance(subject, str) or not isinstance(body, str):
        return {"error": "subject and body must be strings."}, 400

    workflow = db.session.get(Workflow, workflow_id)

    if workflow is None:
        return {"error": "Workflow not found."}, 404

    result = execute_workflow(
        workflow,
        {
            "subject": subject,
            "body": body
        }
    )

    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "result": result
    }, 200
"""
    

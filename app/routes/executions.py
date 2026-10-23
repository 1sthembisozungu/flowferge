# this route receice the request, validates the email data, find the workflow and delegates the actual work to execute_workflow()

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

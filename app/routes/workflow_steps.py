
from flask import Blueprint, request
from app import db
# import SQLAlchemy database object
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep

# workflow model - represent a database table through python

workflow_steps_bp = Blueprint("workflow_steps", __name__)

# blueprint() lets us group releted API routes in a separate file
# request gives us access to the HTTP request sent by the client


@workflow_steps_bp.route(
    "/api/workflows/<int:workflow_id>/steps",
    methods=["POST"]
)
def create_workflow_step(workflow_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "A JSON object is required."}, 400

    step_type = data.get("step_type")
    step_order = data.get("step_order")
    configuration = data.get("configuration")

    if step_type not in ("trigger", "condition", "action"):
        return {
            "error": "step_type must be trigger, condition, or action."
        }, 400

    if (
        isinstance(step_order, bool)
        or not isinstance(step_order, int)
        or step_order < 1
    ):
        return {"error": "step_order must be a positive integer."}, 400

    if not isinstance(configuration, dict):
        return {"error": "configuration must be a JSON object."}, 400

    workflow = db.session.get(Workflow, workflow_id)

    if workflow is None:
        return {"error": "Workflow not found."}, 404

    existing_step = WorkflowStep.query.filter_by(
        workflow_id=workflow_id,
        step_order=step_order
    ).first()

    if existing_step is not None:
        return {
            "error": "This workflow already has a step at that position."
        }, 409

    step = WorkflowStep(
        workflow_id=workflow_id,
        step_type=step_type,
        step_order=step_order,
        configuration=configuration
    )

    try:
        db.session.add(step)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {
        "message": "Workflow step created successfully.",
        "step": {
            "id": step.id,
            "workflow_id": step.workflow_id,
            "step_type": step.step_type,
            "step_order": step.step_order,
            "configuration": step.configuration
        }
    }, 201


from flask import Blueprint, request, current_app

from app import db
from app.models.user import User
from app.models.workflow import Workflow


workflows_bp = Blueprint("workflows", __name__)


@workflows_bp.route("/api/workflows", methods=["GET"])
def get_workflows():
    workflows = Workflow.query.order_by(
        Workflow.created_at.desc()
    ).all()

    return {
        "workflows": [
            {
                "id": workflow.id,
                "user_id": workflow.user_id,
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat()
            }
            for workflow in workflows
        ]
    }, 200


@workflows_bp.route("/api/workflows", methods=["POST"])
def create_workflow():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "A JSON object is required."}, 400

    user_id = data.get("user_id")
    name = data.get("name")
    description = data.get("description", "")
    status = data.get("status", "active")

    if isinstance(user_id, bool) or not isinstance(user_id, int):
        return {"error": "user_id must be an integer."}, 400

    if not isinstance(name, str) or not name.strip():
        return {"error": "A workflow name is required."}, 400

    if len(name.strip()) > 255:
        return {"error": "Workflow name must be 255 characters or fewer."}, 400

    if not isinstance(description, str):
        return {"error": "description must be a string."}, 400

    if status not in ("active", "inactive"):
        return {"error": "status must be active or inactive."}, 400

    user = db.session.get(User, user_id)

    if user is None:
        return {"error": "The specified user does not exist."}, 404

    workflow = Workflow(
        user_id=user.id,
        name=name.strip(),
        description=description.strip(),
        status=status
    )

    try:
        db.session.add(workflow)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create workflow")
        return {"error": "Could not save the workflow."}, 500

    return {
        "message": "Workflow created successfully.",
        "workflow": {
            "id": workflow.id,
            "user_id": workflow.user_id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat()
        }
    }, 201

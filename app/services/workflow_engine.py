# this file contain logic for interpreting and executing the saved steps
from app.models.workflow_step import WorkflowStep


def execute_workflow(workflow, email):
    # An inactive workflow must not run.
    if workflow.status != "active":
        return {
            "status": "skipped",
            "reason": "Workflow is inactive.",
            "action_executed": False
        }

    # Load the steps in the order they should run.
    steps = WorkflowStep.query.filter_by(
        workflow_id=workflow.id
    ).order_by(
        WorkflowStep.step_order.asc()
    ).all()  #***

    if not steps:
        return {
            "status": "failed",
            "reason": "Workflow has no steps.",
            "action_executed": False
        }

    # Confirm that the workflow has the expected structure.
    expected_types = ["trigger", "condition", "action"]
    actual_types = [step.step_type for step in steps]

    if actual_types != expected_types:
        return {
            "status": "failed",
            "reason": "Workflow must contain a trigger, condition, and action in that order.",
            "action_executed": False
        }

    trigger = steps[0]
    condition = steps[1]
    action = steps[2]

    # Step 1: Check the trigger.
    if trigger.configuration.get("event") != "email_received":
        return {
            "status": "skipped",
            "reason": "Unsupported trigger event.",
            "action_executed": False
        }

    # Step 2: Evaluate the condition.
    config = condition.configuration

    field = config.get("field")
    operator = config.get("operator")
    expected_value = config.get("value")

    if field not in ("subject", "body"):
        return {
            "status": "failed",
            "reason": "Condition field must be subject or body.",
            "action_executed": False
        }

    if operator != "contains" or not isinstance(expected_value, str):
        return {
            "status": "failed",
            "reason": "Unsupported condition configuration.",
            "action_executed": False
        }

    actual_value = email.get(field, "")

    if not isinstance(actual_value, str):
        return {
            "status": "failed",
            "reason": "Email subject and body must be strings.",
            "action_executed": False
        }

    matched = expected_value.casefold() in actual_value.casefold()

    if not matched:
        return {
            "status": "completed",
            "condition_matched": False,
            "reason": f"The {field} does not contain '{expected_value}'.",
            "action_executed": False
        }

    # Step 3: Execute the simulated action.
    action_config = action.configuration

    if action_config.get("type") != "log_message":
        return {
            "status": "failed",
            "reason": "Unsupported action type.",
            "action_executed": False
        }

    message = action_config.get("message")

    if not isinstance(message, str) or not message.strip():
        return {
            "status": "failed",
            "reason": "Action message is missing.",
            "action_executed": False
        }

    return {
        "status": "completed",
        "condition_matched": True,
        "reason": "Condition matched.",
        "action_executed": True,
        "action_result": {
            "type": "log_message",
            "message": message
        }
    }

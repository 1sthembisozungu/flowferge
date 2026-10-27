
"use strict";

// Find the HTML elements that the dashboard needs to update.
const totalWorkflowsElement = document.getElementById("total-workflows");
const activeWorkflowsElement = document.getElementById("active-workflows");
const totalExecutionsElement = document.getElementById("total-executions");

const workflowListElement = document.getElementById("workflow-list");
const workflowSelectElement = document.getElementById("workflow-id");
const workflowMessageElement = document.getElementById("workflow-message");

const executionForm = document.getElementById("execution-form");
const executeButton = document.getElementById("execute-button");
const executionResultElement = document.getElementById("execution-result");
const executionResultContent = document.getElementById("execution-result-content");

const historyMessageElement = document.getElementById("history-message");
const historyTableBody = document.getElementById("history-table-body");

// Store the workflows retrieved from Flask.
let workflows = [];

// Safely create an HTML element and set its text.
function createTextElement(tagName, text, className = "") {
    const element = document.createElement(tagName);
    element.textContent = text;

    if (className) {
        element.className = className;
    }

    return element;
}

// Convert an API date into a readable date and time.
function formatDate(dateValue) {
    if (!dateValue) {
        return "—";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return "Invalid date";
    }

    return date.toLocaleString();
}

// Read a JSON response and report unsuccessful HTTP responses.
async function getResponseData(response) {
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "The request failed.");
    }

    return data;
}

// Load workflows from the Flask API.
async function loadWorkflows() {
    workflowMessageElement.textContent = "Loading workflows...";

    try {
        const response = await fetch("/api/workflows");
        const data = await getResponseData(response);

        workflows = Array.isArray(data.workflows) ? data.workflows : [];

        // Update the overview cards.
        totalWorkflowsElement.textContent = workflows.length;

        activeWorkflowsElement.textContent = workflows.filter(
            workflow => workflow.status === "active"
        ).length;

        // Rebuild the workflow dropdown and workflow list.
        workflowSelectElement.replaceChildren(
            createTextElement("option", "Select a workflow")
        );
        workflowSelectElement.options[0].value = "";

        workflowListElement.replaceChildren();

        if (workflows.length === 0) {
            workflowMessageElement.textContent =
                "No workflows found. Create a workflow through the API first.";

            totalExecutionsElement.textContent = "0";
            historyTableBody.replaceChildren();
            historyMessageElement.textContent = "No workflow selected.";
            return;
        }

        workflowMessageElement.textContent =
            `${workflows.length} workflow(s) loaded successfully.`;

        workflows.forEach(workflow => {
            // Add this workflow to the dropdown.
            const option = createTextElement("option", workflow.name);
            option.value = workflow.id;
            workflowSelectElement.appendChild(option);

            // Create a card for the workflow.
            const card = createTextElement("article", "", "workflow-card");
            const details = createTextElement("div", "", "workflow-details");
            const name = createTextElement("h3", workflow.name);
            const description = createTextElement(
                "p",
                workflow.description || "No description provided."
            );
            const status = createTextElement(
                "span",
                workflow.status,
                `status-badge ${workflow.status}`
            );

            details.append(name, description);
            card.append(details, status);

            const actions = createTextElement("div", "", "workflow-actions");

            const testButton = createTextElement("button", "Test workflow", "button primary");
            testButton.type = "button";
            testButton.addEventListener("click", () => {
                workflowSelectElement.value = String(workflow.id);
                document.getElementById("test-workflow").scrollIntoView({
                    behavior: "smooth"
                });
                loadExecutionHistory(workflow.id);
            });

            const historyButton = createTextElement(
                "button",
                "View history",
                "button secondary"
            );
            historyButton.type = "button";
            historyButton.addEventListener("click", () => {
                workflowSelectElement.value = String(workflow.id);
                loadExecutionHistory(workflow.id);
                document.getElementById("history").scrollIntoView({
                    behavior: "smooth"
                });
            });

            actions.append(testButton, historyButton);
            card.appendChild(actions);
            workflowListElement.appendChild(card);
        });

        // Keep the current selection if it still exists.
        const currentSelection = workflows.find(
            workflow => String(workflow.id) === workflowSelectElement.value
        );

        if (!currentSelection) {
            workflowSelectElement.value = "";
            totalExecutionsElement.textContent = "0";
            historyTableBody.replaceChildren();
            historyMessageElement.textContent =
                "Select a workflow to view its history.";
        } else {
            await loadExecutionHistory(currentSelection.id);
        }
    } catch (error) {
        workflowMessageElement.textContent =
            `Could not load workflows: ${error.message}`;
    }
}

// Load execution history for one workflow.
async function loadExecutionHistory(workflowId) {
    if (!workflowId) {
        totalExecutionsElement.textContent = "0";
        historyTableBody.replaceChildren();
        historyMessageElement.textContent =
            "Select a workflow to view its history.";
        return;
    }

    historyMessageElement.textContent = "Loading execution history...";
    historyTableBody.replaceChildren();

    try {
        const response = await fetch(
            `/api/workflows/${encodeURIComponent(workflowId)}/executions`
        );

        const data = await getResponseData(response);
        const executions = Array.isArray(data.executions) ? data.executions : [];

        // This count is for the selected workflow's returned history.
        totalExecutionsElement.textContent =
            data.count ?? executions.length;

        if (executions.length === 0) {
            historyMessageElement.textContent =
                "This workflow has no recorded executions yet.";
            return;
        }

        historyMessageElement.textContent =
            `Showing ${executions.length} recent execution(s) for ${data.workflow_name}.`;

        executions.forEach(execution => {
            const row = document.createElement("tr");

            row.append(
                createTextElement("td", String(execution.id)),
                createTextElement(
                    "td",
                    execution.status || "unknown",
                    `execution-status ${execution.status || ""}`
                ),
                createTextElement("td", formatDate(execution.started_at)),
                createTextElement("td", formatDate(execution.finished_at))
            );

            historyTableBody.appendChild(row);
        });
    } catch (error) {
        totalExecutionsElement.textContent = "—";
        historyMessageElement.textContent =
            `Could not load execution history: ${error.message}`;
    }
}

// Send the simulated email to the selected workflow.
executionForm.addEventListener("submit", async event => {
    event.preventDefault();

    const workflowId = workflowSelectElement.value;
    const subject = document.getElementById("email-subject").value.trim();
    const body = document.getElementById("email-body").value.trim();

    if (!workflowId) {
        historyMessageElement.textContent = "Please select a workflow first.";
        return;
    }

    executeButton.disabled = true;
    executeButton.textContent = "Running...";
    executionResultElement.hidden = true;

    try {
        const response = await fetch(
            `/api/workflows/${encodeURIComponent(workflowId)}/execute`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ subject, body })
            }
        );

        const data = await getResponseData(response);

        // Display the complete response, including the engine's result.
        executionResultContent.textContent =
            JSON.stringify(data, null, 2);

        executionResultElement.hidden = false;

        // Reload the saved history after the run finishes.
        await loadExecutionHistory(workflowId);
    } catch (error) {
        executionResultContent.textContent = JSON.stringify(
            { error: error.message },
            null,
            2
        );

        executionResultElement.hidden = false;
    } finally {
        executeButton.disabled = false;
        executeButton.textContent = "Run workflow";
    }
});

// Load history whenever the selected workflow changes.
workflowSelectElement.addEventListener("change", () => {
    loadExecutionHistory(workflowSelectElement.value);
});

// Connect the refresh buttons.
document.getElementById("refresh-workflows").addEventListener("click", () => {
    loadWorkflows();
});

document.getElementById("refresh-history").addEventListener("click", () => {
    loadExecutionHistory(workflowSelectElement.value);
});

// Make the execution card's meaning clear.
const executionCard = totalExecutionsElement.closest(".stat-card");
if (executionCard) {
    const description = executionCard.querySelector("span");

    if (description) {
        description.textContent = "For the selected workflow";
    }
}

// Load data when the dashboard first opens.
loadWorkflows();

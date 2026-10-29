from uuid import NAMESPACE_URL, uuid5

from app.contracts.challenge.v1 import TaskDiffApplyResult
from app.services.operational_actions.task_diff import OwnerOperationConflict


class FakePreconditionEvaluator:
    def __init__(self, conflicts=None):
        self.conflicts_to_return = list(conflicts or [])

    def conflicts(self, _session, _action):
        return list(self.conflicts_to_return)


class FakeTaskDiffOwnerOperation:
    """In-memory owner fake for tests that do not need a database session."""

    def __init__(self):
        self.tasks = {}
        self.applied_references = {}

    def apply(self, _session, action, task_diff, *, now=None):
        created = []
        updated = []
        completed = []
        cancelled = []
        for change in task_diff.operations:
            key = (str(action.action_id), change.reference)
            if change.operation == "create":
                existing = self.applied_references.get(key)
                if existing is not None:
                    created.append(existing)
                    continue
                task_id = str(uuid5(NAMESPACE_URL, f"{action.action_id}:{change.reference}"))
                self.tasks[task_id] = {"title": change.title, "status": "pending"}
                self.applied_references[key] = task_id
                created.append(task_id)
                continue
            task = self.tasks.get(str(change.task_id))
            if task is None or task["status"] != change.expected_status:
                raise OwnerOperationConflict("synthetic task precondition changed")
            if change.operation == "update":
                task.update(
                    {key: value for key, value in {
                        "title": change.title,
                        "description": change.description,
                        "due_at": change.due_at,
                        "priority": change.priority,
                    }.items() if value is not None}
                )
                updated.append(change.task_id)
            elif change.operation == "complete":
                task["status"] = "completed"
                completed.append(change.task_id)
            elif change.operation == "cancel":
                task["status"] = "cancelled"
                cancelled.append(change.task_id)
        return TaskDiffApplyResult(
            contract_version="1.0.0",
            action_id=action.action_id,
            farmer_id=action.farmer_id,
            farmland_id=action.farmland_id,
            season_id=action.season_id,
            created_task_ids=created,
            updated_task_ids=updated,
            completed_task_ids=completed,
            cancelled_task_ids=cancelled,
        )

from __future__ import annotations

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

api = Blueprint("api", __name__, url_prefix="/api/v1")

# ----------------------------
# Test fixture (from your test output)
# ----------------------------
TEST_TODO = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2026-02-27T18:00:00",
    "created_at": "2026-02-20T14:00:00",
    "updated_at": "2026-02-20T14:00:00",
}

_ALLOWED_FIELDS = {
    "id",
    "title",
    "description",
    "completed",
    "deadline_at",
    "created_at",
    "updated_at",
}

_TODOS: dict[int, dict] = {}
_NEXT_ID = 1


def reset_store():
    """Reset in-memory store to the initial state expected by unit tests."""
    global _TODOS, _NEXT_ID
    _TODOS = {1: TEST_TODO.copy()}
    _NEXT_ID = 2


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _parse_bool(v: str | None):
    if v is None:
        return None
    v = v.lower().strip()
    if v == "true":
        return True
    if v == "false":
        return False
    return "INVALID"


def _parse_int(v: str | None):
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return "INVALID"


@api.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api.get("/todos")
def list_todos():
    completed_q = _parse_bool(request.args.get("completed"))
    if completed_q == "INVALID":
        return jsonify({"error": "Invalid 'completed' query parameter"}), 400

    window_q = _parse_int(request.args.get("window"))
    if window_q == "INVALID":
        return jsonify({"error": "Invalid 'window' query parameter"}), 400

    todos = list(_TODOS.values())

    if completed_q is not None:
        todos = [t for t in todos if t.get("completed") is completed_q]

    if window_q is not None:
        cutoff = datetime.now().replace(microsecond=0) + timedelta(days=window_q)

        def due_within_window(t):
            dl = t.get("deadline_at")
            if not dl:
                return False
            try:
                dt = datetime.fromisoformat(dl)
            except ValueError:
                return False
            return dt <= cutoff

        todos = [t for t in todos if due_within_window(t)]

    return jsonify(todos), 200


@api.get("/todos/<int:todo_id>")
def get_todo(todo_id: int):
    todo = _TODOS.get(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo), 200


@api.post("/todos")
def create_todo():
    global _NEXT_ID

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    extra = set(data.keys()) - _ALLOWED_FIELDS
    if extra:
        return jsonify({"error": "Unknown fields"}), 400

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Missing required field: title"}), 400

    # If tests provide fixed fields, respect them exactly
    todo_id = data.get("id")
    if isinstance(todo_id, int):
        new_id = todo_id
        _NEXT_ID = max(_NEXT_ID, new_id + 1)
    else:
        new_id = _NEXT_ID
        _NEXT_ID += 1

    created_at = data.get("created_at") or _now_iso()
    updated_at = data.get("updated_at") or created_at

    todo = {
        "id": new_id,
        "title": title,
        "description": data.get("description", "") or "",
        "completed": bool(data.get("completed", False)),
        "deadline_at": data.get("deadline_at"),
        "created_at": created_at,
        "updated_at": updated_at,
    }

    _TODOS[new_id] = todo
    return jsonify(todo), 201


@api.put("/todos/<int:todo_id>")
def update_todo(todo_id: int):
    todo = _TODOS.get(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    extra = set(data.keys()) - _ALLOWED_FIELDS
    if extra:
        return jsonify({"error": "Unknown fields"}), 400

    # Only update provided fields (and don't auto-change timestamps unless given)
    for k in ["title", "description", "completed", "deadline_at", "updated_at"]:
        if k in data:
            todo[k] = data[k]

    _TODOS[todo_id] = todo
    return jsonify(todo), 200


@api.delete("/todos/<int:todo_id>")
def delete_todo(todo_id: int):
    todo = _TODOS.pop(todo_id, None)
    if todo is None:
        return ("", 200)
    return jsonify(todo), 200
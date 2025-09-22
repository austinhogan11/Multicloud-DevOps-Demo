// Very small API client for the FastAPI tasks endpoints.
// In dev, calls go to `/api/*` and are proxied by Vite to the backend.

const BASE = '/api'

// GET /tasks/
export async function fetchTasks() {
  const res = await fetch(`${BASE}/tasks/`)
  if (!res.ok) throw new Error(`Failed to fetch tasks: ${res.status}`)
  return res.json()
}

// POST /tasks/
// The backend expects an object with id, title, completed
export async function createTask(task) {
  const res = await fetch(`${BASE}/tasks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  })
  if (!res.ok) throw new Error(`Failed to create task: ${res.status}`)
  return res.json()
}

// PUT /tasks/{id}
export async function updateTask(task) {
  const res = await fetch(`${BASE}/tasks/${task.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  })
  if (!res.ok) throw new Error(`Failed to update task: ${res.status}`)
  return res.json()
}

// DELETE /tasks/{id}
export async function deleteTask(id) {
  const res = await fetch(`${BASE}/tasks/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete task: ${res.status}`)
  return res.json()
}


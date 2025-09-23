// Very small API client for the FastAPI tasks endpoints.
// Dev: Vite proxy forwards `/api/*` to the backend.
// Prod (S3/CloudFront): set `VITE_API_BASE` to your API Gateway/Lambda URL.

const RAW_BASE = import.meta.env.VITE_API_BASE || '/api'
const BASE = RAW_BASE.replace(/\/$/, '') // trim trailing slash

async function request(path, init) {
  const url = `${BASE}${path}`
  const res = await fetch(url, init)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} for ${url}${text ? `: ${text.slice(0,120)}` : ''}`)
  }
  return res.json()
}

// GET /tasks/
export async function fetchTasks() {
  return request(`/tasks/`)
}

// POST /tasks/
// The backend expects an object with id, title, completed
export async function createTask(task) {
  return request(`/tasks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  })
}

// PUT /tasks/{id}
export async function updateTask(task) {
  return request(`/tasks/${task.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  })
}

// DELETE /tasks/{id}
export async function deleteTask(id) {
  return request(`/tasks/${id}`, { method: 'DELETE' })
}

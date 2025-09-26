// Simple per-visitor persistence using localStorage
const KEY_TASKS = 'tasks_v1'
const KEY_ANON = 'anon_id_v1'

export function getAnonId() {
  try {
    let id = localStorage.getItem(KEY_ANON)
    if (!id) {
      id = crypto?.randomUUID?.() || Math.random().toString(36).slice(2)
      localStorage.setItem(KEY_ANON, id)
    }
    return id
  } catch (_) {
    return 'anon'
  }
}

export function loadTasks() {
  try {
    const raw = localStorage.getItem(KEY_TASKS)
    if (!raw) return []
    const data = JSON.parse(raw)
    if (Array.isArray(data)) return data
    return []
  } catch (_) {
    return []
  }
}

export function saveTasks(tasks) {
  try {
    localStorage.setItem(KEY_TASKS, JSON.stringify(tasks))
  } catch (_) {
    // ignore write errors (private mode/quota)
  }
}


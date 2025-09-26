// Todo page: shows list, edit/delete, and add form
import { useEffect, useMemo, useState } from 'react'
import TodoItem from '../components/TodoItem.jsx'
import { fetchTasks, createTask, updateTask, deleteTask as apiDeleteTask } from '../lib/api.js'
import { loadTasks, saveTasks, getAnonId } from '../lib/storage.js'
import { track } from '../lib/analytics.js'

export default function TodoPage() {
  // Tasks from the API
  const [todos, setTodos] = useState([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Count tasks not completed
  const remaining = useMemo(() => todos.filter(t => !t.completed).length, [todos])

  // Local-first: load tasks from localStorage on mount
  useEffect(() => {
    setLoading(true)
    const cached = loadTasks()
    setTodos(cached)
    setLoading(false)
    getAnonId() // ensure we have a stable anon id for this browser
  }, [])

  // Add a new task
  function addTodo(e) {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return
    // Backend expects an id on create; use next available
    const id = Math.max(0, ...todos.map(t => t.id)) + 1
    const optimistic = { id, title, completed: false }
    const nextTasks = [...todos, optimistic]
    setTodos(nextTasks)
    saveTasks(nextTasks)
    setNewTitle('')
    // Best-effort sync to backend; do not revert local cache on failure
    createTask(optimistic).then(() => {
      track('task_created', { title_len: title.length })
    }).catch((e) => {
      setError(e.message || 'Failed to add task')
      track('task_create_failed')
    })
  }

  // Remove a task
  function deleteTodo(todo) {
    const nextTasks = todos.filter(t => t.id !== todo.id)
    setTodos(nextTasks)
    saveTasks(nextTasks)
    apiDeleteTask(todo.id).then(() => {
      track('task_deleted')
    }).catch((e) => {
      setError(e.message || 'Failed to delete task')
      track('task_delete_failed')
    })
  }

  // Toggle completed flag
  function toggleTodo(todo) {
    const next = { ...todo, completed: !todo.completed }
    const nextTasks = todos.map(t => (t.id === todo.id ? next : t))
    setTodos(nextTasks)
    saveTasks(nextTasks)
    updateTask(next).then(() => {
      track(next.completed ? 'task_completed' : 'task_uncompleted')
    }).catch((e) => {
      setError(e.message || 'Failed to update task')
      track('task_toggle_failed')
    })
  }

  // Very simple edit using prompt
  function editTodo(todo) {
    const title = prompt('Edit task title', todo.title)
    if (title == null) return
    const next = title.trim()
    if (!next) return
    const updated = { ...todo, title: next }
    const nextTasks = todos.map(t => (t.id === todo.id ? updated : t))
    setTodos(nextTasks)
    saveTasks(nextTasks)
    updateTask(updated).then(() => {
      track('task_edited', { title_len: updated.title.length })
    }).catch((e) => {
      setError(e.message || 'Failed to update task')
      track('task_edit_failed')
    })
  }

  return (
    <div className="container mx-auto px-4">
      {/* Title above card */}
      <div className="text-center mt-10 mb-4">
        <h2 className="text-2xl font-semibold tracking-tight">Your Tasks</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">{remaining} remaining</p>
      </div>

      {/* Card centered on page */}
      <div className="max-w-xl mx-auto">
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-charcoal/70 shadow-sm backdrop-blur p-4">
          <ul className="divide-y divide-gray-200 dark:divide-gray-800">
            {loading && (
              <li className="py-6 text-center text-gray-500 dark:text-gray-400">Loading…</li>
            )}
            {!!error && !loading && (
              <li className="py-3 text-center text-red-600 dark:text-red-400 text-sm">{error}</li>
            )}
            {todos.length === 0 ? (
              <li className="py-6 text-center text-gray-500 dark:text-gray-400">No tasks yet</li>
            ) : (
              todos.map(todo => (
                <TodoItem
                  key={todo.id}
                  todo={todo}
                  onEdit={editTodo}
                  onDelete={deleteTodo}
                  onToggle={toggleTodo}
                />
              ))
            )}
          </ul>
        </div>

        {/* Add item under the card */}
        <form onSubmit={addTodo} className="mt-4 flex gap-2">
          <input
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            placeholder="Add a new task"
            className="flex-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-charcoal px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <button
            type="submit"
            className="rounded-md bg-accent text-white px-4 py-2 text-sm font-medium hover:bg-accent-2 transition-colors focus:outline-none focus:ring-2 focus:ring-accent"
          >
            Add
          </button>
        </form>
      </div>
    </div>
  )
}

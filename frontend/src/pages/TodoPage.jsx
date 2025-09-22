// Todo page: shows list, edit/delete, and add form
import { useMemo, useState } from 'react'
import TodoItem from '../components/TodoItem.jsx'

export default function TodoPage() {
  // Local sample data. Replace with API calls later.
  const [todos, setTodos] = useState([
    { id: 1, title: 'Buy milk', completed: false },
    { id: 2, title: 'Read a book', completed: true },
  ])
  const [newTitle, setNewTitle] = useState('')

  // Count tasks not completed
  const remaining = useMemo(() => todos.filter(t => !t.completed).length, [todos])

  // Add a new task
  function addTodo(e) {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return
    const id = Math.max(0, ...todos.map(t => t.id)) + 1
    setTodos(prev => [...prev, { id, title, completed: false }])
    setNewTitle('')
  }

  // Remove a task
  function deleteTodo(todo) {
    setTodos(prev => prev.filter(t => t.id !== todo.id))
  }

  // Toggle completed flag
  function toggleTodo(todo) {
    setTodos(prev => prev.map(t => (t.id === todo.id ? { ...t, completed: !t.completed } : t)))
  }

  // Very simple edit using prompt
  function editTodo(todo) {
    const title = prompt('Edit task title', todo.title)
    if (title == null) return
    const next = title.trim()
    if (!next) return
    setTodos(prev => prev.map(t => (t.id === todo.id ? { ...t, title: next } : t)))
  }

  return (
    <div className="container mx-auto px-4">
      {/* Title above card */
      }
      <div className="text-center mt-10 mb-4">
        <h2 className="text-2xl font-semibold tracking-tight">Your Tasks</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">{remaining} remaining</p>
      </div>

      {/* Card centered on page */}
      <div className="max-w-xl mx-auto">
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-charcoal/70 shadow-sm backdrop-blur p-4">
          <ul className="divide-y divide-gray-200 dark:divide-gray-800">
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

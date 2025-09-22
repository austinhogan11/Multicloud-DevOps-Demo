// A single todo row with checkbox + edit + delete actions
export default function TodoItem({ todo, onEdit, onDelete, onToggle }) {
  return (
    <li className="flex items-center gap-3 py-2">
      {/* Complete toggle */}
      <input
        type="checkbox"
        className="size-4 accent-accent cursor-pointer"
        checked={todo.completed}
        onChange={() => onToggle?.(todo)}
      />

      {/* Task title; strike-through when completed */}
      <span className={`flex-1 ${todo.completed ? 'line-through text-gray-500 dark:text-gray-400' : ''}`}>
        {todo.title}
      </span>

      {/* Edit button (pen). Neutral color; orange glow on hover */}
      <button
        type="button"
        className="p-1 rounded text-gray-500 dark:text-gray-400 hover:text-accent hover:drop-shadow-[0_0_8px_#ea6a1c] transition"
        onClick={() => onEdit?.(todo)}
        aria-label="Edit"
        title="Edit"
      >
        {/* Pen icon (outline, simple) */}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="size-5">
          <path d="M15.232 5.232 18.768 8.768"/>
          <path d="M4 20l3.5-.875a2 2 0 0 0 .96-.54l8.71-8.71a2 2 0 0 0 0-2.829L16.955 5.1a2 2 0 0 0-2.829 0l-8.71 8.71a2 2 0 0 0-.54.96L4 20z"/>
        </svg>
      </button>

      {/* Delete button (X). Neutral color; orange glow on hover */}
      <button
        type="button"
        className="p-1 rounded text-gray-500 dark:text-gray-400 hover:text-accent hover:drop-shadow-[0_0_8px_#ea6a1c] transition"
        onClick={() => onDelete?.(todo)}
        aria-label="Delete"
        title="Delete"
      >
        {/* X icon (outline, simple) */}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="size-5">
          <path d="M6 6l12 12M18 6l-12 12"/>
        </svg>
      </button>
    </li>
  )
}

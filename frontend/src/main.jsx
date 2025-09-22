// Entry point: renders the React app
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css' // Tailwind and base styles
import App from './App.jsx'

// Mount the app in the page
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

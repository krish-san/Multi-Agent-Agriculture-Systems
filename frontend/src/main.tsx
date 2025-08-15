import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { RouterProvider } from 'react-router-dom'
import router from './router'

createRoot(document.getElementById('root')!).render(
  // Temporarily disable StrictMode to fix WebSocket connection issues in development
  // <React.StrictMode>
    <RouterProvider router={router} />
  // </React.StrictMode>
)

import { useState } from 'react'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  if (isAuthenticated) {
    return <DashboardPage />
  }

  return <LoginPage onLogin={handleLogin} />
}

export default App

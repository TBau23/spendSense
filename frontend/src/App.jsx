import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import OperatorDashboard from './pages/OperatorDashboard'
import UserDetailView from './pages/UserDetailView'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<Navigate to="/operator" replace />} />
        <Route path="/operator" element={<OperatorDashboard />} />
        <Route path="/operator/users/:userId" element={<UserDetailView />} />
      </Routes>
    </div>
  )
}

export default App

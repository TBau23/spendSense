import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import OperatorDashboard from './pages/OperatorDashboard'
import UserDetailView from './pages/UserDetailView'
import UserLanding from './pages/UserLanding'
import UserPortal from './pages/UserPortal'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<Navigate to="/user" replace />} />
        <Route path="/operator" element={<OperatorDashboard />} />
        <Route path="/operator/users/:userId" element={<UserDetailView />} />
        <Route path="/user" element={<UserLanding />} />
        <Route path="/user/:userId" element={<UserPortal />} />
      </Routes>
    </div>
  )
}

export default App

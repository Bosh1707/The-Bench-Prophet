import React, { useEffect, useState } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { auth } from './firebase';
import Login from './Login';
import Signup from './signup';
import Dashboard from './components/PredictionDashboard';
import TeamComparison from './components/TeamComparison';
import Navbar from './components/Navbar';
import { ConfigProvider } from 'antd';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  if (loading) return <div className="loading-spinner">Loading...</div>;

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff', // Default Ant Design primary color
          borderRadius: 4, // Default border radius
        },
      }}
    >
      <Router>
        {user && <Navbar user={user} />}
        <div className="app-content">
          <Routes>
            <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
            <Route path="/signup" element={user ? <Navigate to="/dashboard" /> : <Signup />} />
            <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
            <Route path="/compare" element={user ? <TeamComparison /> : <Navigate to="/login" />} />
            <Route path="*" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;
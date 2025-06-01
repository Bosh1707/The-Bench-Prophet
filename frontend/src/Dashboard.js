import React from 'react';
import { signOut } from 'firebase/auth';
import { auth } from './firebase';
import './App.css';

export default function Dashboard({ user }) {
  const handleLogout = () => {
    signOut(auth).then(() => {
      alert('Logged out!');
    });
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">The Bench Prophet</div>
        <div className="navbar-user">
          <span>{user.email}</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="dashboard-content">
        <h2>Welcome, {user.email}</h2>
        <p>You are logged in to The Bench Prophet dashboard!</p>
      </div>
    </>
  );
}

import React from 'react';
import { signOut } from 'firebase/auth';
import { auth } from './firebase';

export default function Dashboard({ user }) {
  const handleLogout = () => {
    signOut(auth).then(() => {
      alert('Logged out!');
    });
  };

  return (
    <div>
      <h1>Welcome, {user.email}</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}

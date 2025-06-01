import React, { useState } from 'react';
import { createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from './firebase';
import { Link } from 'react-router-dom';
import './App.css';

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      // Sign up success, redirection will occur via onAuthStateChanged
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={handleSignup}>
      <h2>Sign Up</h2>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
      <button type="submit">Sign Up</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div className="link-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </div>
    </form>
  );
}

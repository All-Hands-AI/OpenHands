import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [number, setNumber] = useState('');

  useEffect(() => {
    fetch('http://localhost:3000/random')
      .then(response => response.json())
      .then(data => setNumber(data.number))
      .catch(err => console.error('Error fetching the number:', err));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>The random number from API is: {number}</p>
      </header>
    </div>
  );
}

export default App;
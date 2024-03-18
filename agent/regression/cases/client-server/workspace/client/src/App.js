import React, { useState, useEffect } from 'react';

function App() {
  const [number, setNumber] = useState('Loading...');

  useEffect(() => {
    fetch('/random')
      .then(response => response.json())
      .then(data => setNumber(data.number))
      .catch(error => console.error('Error fetching number:', error));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>
          Random Number: {number}
        </p>
      </header>
    </div>
  );
}

export default App;

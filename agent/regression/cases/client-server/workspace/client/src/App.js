import React, { useEffect, useState } from 'react';

function App() {
  const [number, setNumber] = useState('');

  useEffect(() => {
    console.log('Fetching random number...');
    fetch('/random')
      .then(response => response.json())
      .then(data => {
        console.log('Data received:', data);
        setNumber(data.number);
      })
      .catch(error => console.error('Fetch error:', error));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <p>The random number is: {number}</p>
      </header>
    </div>
  );
}

export default App;

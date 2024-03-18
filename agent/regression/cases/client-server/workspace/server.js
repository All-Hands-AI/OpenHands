const express = require('express');
const app = express();
const port = 3001;

app.get('/random', (req, res) => {
  res.json({ number: Math.floor(Math.random() * 100) });
});

app.listen(port, () => {
  console.log(`API server listening at http://localhost:${port}`);
});
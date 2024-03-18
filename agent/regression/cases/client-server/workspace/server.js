const express = require('express');
const app = express();
const port = 3000;

app.get('/random', (req, res) => {
  const randomNumber = Math.floor(Math.random() * 10000);
  res.json({ number: randomNumber });
});

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`);
});
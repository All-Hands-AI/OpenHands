function spongebobCase(inputString) {
  return inputString.split('').map((char, index) => index % 2 === 0 ? char.toLowerCase() : char.toUpperCase()).join('');
}

module.exports = spongebobCase;
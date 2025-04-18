export const getRandomKey = (obj: Record<string, string>) => {
  const keys = Object.keys(obj);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];

  return randomKey;
};

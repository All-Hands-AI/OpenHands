const beep = () => {
  const snd = new Audio("/beep.wav");
  snd.addEventListener("canplaythrough", () => snd.play());
};

export default beep;

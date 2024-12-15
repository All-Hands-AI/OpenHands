interface BrowserSnaphsotProps {
  src: string;
}

export function BrowserSnapshot({ src }: BrowserSnaphsotProps) {
  return (
    <img
      src={src}
      style={{ objectFit: "contain", width: "100%", height: "auto" }}
      className="rounded-xl"
      alt="Browser Screenshot"
    />
  );
}

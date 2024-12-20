import { FaGraduationCap } from "react-icons/fa";

export function DocsButton() {
  return (
    <a
      href="https://docs.all-hands.dev"
      aria-label="Documentation"
      target="_blank"
      rel="noreferrer noopener"
      className="rounded-full hover:opacity-80 flex items-center justify-center"
    >
      <FaGraduationCap fill="#a3a3a3" size={24} />
    </a>
  );
}

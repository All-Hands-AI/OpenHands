import "../../index.css";

type ButtonProps = {
  label?: string;
  primary: boolean;
};
export const Button = ({ label }: ButtonProps) => {
  return (
    <button className="px-4 py-2 bg-avocado-100 text-white rounded hover:bg-blue-700">
      {label}
    </button>
  );
};

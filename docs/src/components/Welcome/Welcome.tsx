import styles from "./styles.module.css";
import "../../pages/index.module.css"
export function Welcome() {
  return (
    <div className="text-white">
      <div className="flex justify-center items-center flex-col md:flex-row bg-gradient-to-b from-slate-600 dark:to-gray-900 to-gray-200">
        <img src="img/logo.png" className="
        max-sm:h-[40vw] max-sm:w-[40vw]
        h-[45vh] w-[45vw]
        md:h-[60vh] md:w-[350px]" />
        <p className=" px-6 md:p-2 mb-6 font-light text-lg md:text-2xl">
          Welcome to OpenDevin, an open-source project aiming to replicate
          Devin, an autonomous AI software engineer who is capable of executing
          complex engineering tasks and collaborating actively with users on
          software development projects. This project aspires to replicate,
          enhance, and innovate upon Devin through the power of the open-source
          community.
        </p>
      </div>
    </div>
  );
}

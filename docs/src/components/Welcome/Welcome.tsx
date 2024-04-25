import styles from "./styles.module.css";

export function Welcome() {
  return (
    <div className={styles.container}>
      <div className={styles.innerContainer}>
        <img src="img/logo.png" className={styles.sidebarImage} />
        <p className={styles.welcomeText}>
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

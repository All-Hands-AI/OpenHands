export function RepoConnector() {
  return (
    <section className="w-full">
      <h2 className="heading">Connect to a Repository</h2>
      <select aria-label="Select a Repo">
        <option>Select a Repo</option>
      </select>
      <button type="button">Launch</button>
      <div>
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitHub repositories
        </a>
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitLab repositories
        </a>
      </div>
    </section>
  );
}

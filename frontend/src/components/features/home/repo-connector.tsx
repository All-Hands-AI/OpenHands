import { BrandButton } from "../settings/brand-button";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";

export function RepoConnector() {
  return (
    <section className="w-full flex flex-col gap-6">
      <h2 className="heading">Connect to a Repository</h2>

      <SettingsDropdownInput
        testId="repo-connector"
        name="repo-connector"
        placeholder="Select a repo"
        items={[
          { key: "1", label: "Repo 1" },
          { key: "2", label: "Repo 2" },
        ]}
      />

      <BrandButton variant="primary" type="button" isDisabled>
        Launch
      </BrandButton>

      <div className="flex flex-col text-sm underline underline-offset-2 text-content-2 gap-4">
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitHub repos
        </a>
        <a href="http://" target="_blank" rel="noopener noreferrer">
          Add GitLab repos
        </a>
      </div>
    </section>
  );
}

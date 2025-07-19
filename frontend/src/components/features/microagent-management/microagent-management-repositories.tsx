import { useTranslation } from "react-i18next";
import { Accordion, AccordionItem } from "@heroui/react";
import { MicroagentManagementRepoMicroagents } from "./microagent-management-repo-microagents";
import { GitRepository } from "#/types/git";
import { getGitProviderBaseUrl } from "#/utils/utils";
import { TabType } from "#/types/microagent-management";
import { MicroagentManagementNoRepositories } from "./microagent-management-no-repositories";
import { I18nKey } from "#/i18n/declaration";
import { DOCUMENTATION_URL } from "#/utils/constants";
import { MicroagentManagementAccordionTitle } from "./microagent-management-accordion-title";

type MicroagentManagementRepositoriesProps = {
  repositories: GitRepository[];
  tabType: TabType;
};

export function MicroagentManagementRepositories({
  repositories,
  tabType,
}: MicroagentManagementRepositoriesProps) {
  const { t } = useTranslation();

  const numberOfRepoMicroagents = repositories.length;

  if (numberOfRepoMicroagents === 0) {
    if (tabType === "personal") {
      return (
        <MicroagentManagementNoRepositories
          title={t(
            I18nKey.MICROAGENT_MANAGEMENT$YOU_DO_NOT_HAVE_USER_LEVEL_MICROAGENTS,
          )}
          documentationUrl={DOCUMENTATION_URL.MICROAGENTS.MICROAGENTS_OVERVIEW}
        />
      );
    }
    if (tabType === "repositories") {
      return (
        <MicroagentManagementNoRepositories
          title={t(I18nKey.MICROAGENT_MANAGEMENT$YOU_DO_NOT_HAVE_MICROAGENTS)}
          documentationUrl={DOCUMENTATION_URL.MICROAGENTS.MICROAGENTS_OVERVIEW}
        />
      );
    }
    if (tabType === "organizations") {
      return (
        <MicroagentManagementNoRepositories
          title={t(
            I18nKey.MICROAGENT_MANAGEMENT$YOU_DO_NOT_HAVE_ORGANIZATION_LEVEL_MICROAGENTS,
          )}
          documentationUrl={
            DOCUMENTATION_URL.MICROAGENTS.ORGANIZATION_AND_USER_MICROAGENTS
          }
        />
      );
    }
  }

  return (
    <Accordion
      variant="splitted"
      className="w-full px-0 gap-3"
      itemClasses={{
        base: "shadow-none bg-transparent border border-[#ffffff40] rounded-[6px] cursor-pointer",
        trigger: "cursor-pointer",
      }}
      selectionMode="multiple"
    >
      {repositories.map((repository) => (
        <AccordionItem
          key={repository.id}
          aria-label={repository.full_name}
          title={<MicroagentManagementAccordionTitle repository={repository} />}
        >
          <MicroagentManagementRepoMicroagents
            repoMicroagent={{
              id: repository.id,
              repositoryName: repository.full_name,
              repositoryUrl: `${getGitProviderBaseUrl(repository.git_provider)}/${repository.full_name}`,
            }}
          />
        </AccordionItem>
      ))}
    </Accordion>
  );
}

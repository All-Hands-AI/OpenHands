import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Accordion, AccordionItem } from "@heroui/react";
import { MicroagentManagementRepoMicroagents } from "./microagent-management-repo-microagents";
import { GitRepository } from "#/types/git";
import { cn } from "#/utils/utils";
import { TabType } from "#/types/microagent-management";
import { MicroagentManagementNoRepositories } from "./microagent-management-no-repositories";
import { I18nKey } from "#/i18n/declaration";
import { DOCUMENTATION_URL } from "#/utils/constants";
import { MicroagentManagementAccordionTitle } from "./microagent-management-accordion-title";
import { sanitizeQuery } from "#/utils/sanitize-query";

type MicroagentManagementRepositoriesProps = {
  repositories: GitRepository[];
  tabType: TabType;
};

export function MicroagentManagementRepositories({
  repositories,
  tabType,
}: MicroagentManagementRepositoriesProps) {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState("");

  const numberOfRepoMicroagents = repositories.length;

  // Filter repositories based on search query
  const filteredRepositories = useMemo(() => {
    if (!searchQuery.trim()) {
      return repositories;
    }

    const sanitizedQuery = sanitizeQuery(searchQuery);
    return repositories.filter((repository) => {
      const sanitizedRepoName = sanitizeQuery(repository.full_name);
      return sanitizedRepoName.includes(sanitizedQuery);
    });
  }, [repositories, searchQuery]);

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
    <div className="flex flex-col gap-4 w-full">
      {/* Search Input */}
      <div className="flex flex-col gap-2 w-full">
        <label htmlFor="repository-search" className="sr-only">
          {t(I18nKey.COMMON$SEARCH_REPOSITORIES)}
        </label>
        <input
          id="repository-search"
          name="repository-search"
          type="text"
          placeholder={`${t(I18nKey.COMMON$SEARCH_REPOSITORIES)}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={cn(
            "bg-tertiary border border-[#717888] bg-[#454545] w-full rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt",
            "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
          )}
        />
      </div>

      {/* Repositories Accordion */}
      <Accordion
        variant="splitted"
        className="w-full px-0 gap-3"
        itemClasses={{
          base: "shadow-none bg-transparent cursor-pointer px-0",
          trigger: "cursor-pointer gap-2 py-3",
          indicator:
            "flex items-center justify-center p-0.5 pr-[3px] text-white hover:bg-[#454545] rounded transition-colors duration-200 rotate-180",
        }}
        selectionMode="multiple"
      >
        {filteredRepositories.map((repository) => (
          <AccordionItem
            key={repository.id}
            aria-label={repository.full_name}
            title={
              <MicroagentManagementAccordionTitle repository={repository} />
            }
          >
            <MicroagentManagementRepoMicroagents repository={repository} />
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}

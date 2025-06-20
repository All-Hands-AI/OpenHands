import { Link } from "react-router";
import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useSettings } from "#/hooks/query/use-settings";
import { Github, GitBranch } from "lucide-react";

export function ConnectToProviderMessage() {
  const { isLoading } = useSettings();
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-content-secondary">{t("HOME$CONNECT_PROVIDER_MESSAGE")}</p>
      <div className="flex gap-3">
        <Link data-testid="navigate-to-settings-button" to="/settings/git">
          <button
            type="button"
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-[#24292e] text-white hover:bg-[#1b1f23]"
          >
            <Github className="w-4 h-4" />
            {!isLoading && "Connect GitHub"}
            {isLoading && t("HOME$LOADING")}
          </button>
        </Link>
        <Link data-testid="navigate-to-settings-button" to="/settings/git">
          <button
            type="button"
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-2 text-sm rounded disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition-colors duration-150 bg-[#fc6d26] text-white hover:bg-[#e24329]"
          >
            <GitBranch className="w-4 h-4" />
            {!isLoading && "Connect GitLab"}
            {isLoading && t("HOME$LOADING")}
          </button>
        </Link>
      </div>
    </div>
  );
}

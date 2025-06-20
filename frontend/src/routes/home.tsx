import React from "react";
import { PrefetchPageLinks } from "react-router";
import { HomeHeader } from "#/components/features/home/home-header";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { useUserProviders } from "#/hooks/use-user-providers";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useTranslation } from "react-i18next";
import { GitBranch, Plus } from "lucide-react";

<PrefetchPageLinks page="/conversations/:conversationId" />;

function HomeScreen() {
  const { providers } = useUserProviders();
  const [selectedRepoTitle, setSelectedRepoTitle] = React.useState<
    string | null
  >(null);
  const { t } = useTranslation();

  const {
    mutate: createConversation,
    isPending,
    isSuccess,
  } = useCreateConversation();
  const isCreatingConversationElsewhere = useIsCreatingConversation();

  const isCreatingConversation =
    isPending || isSuccess || isCreatingConversationElsewhere;

  const providersAreSet = providers.length > 0;

  return (
    <div
      data-testid="home-screen"
      className="h-full flex flex-col rounded-xl px-[42px] pt-[42px] overflow-y-auto"
    >
      <main className="flex-1 flex flex-col items-center justify-center">
        <div className="w-full max-w-4xl mx-auto">
          {/* Header Section with Logo and Title */}
          <header className="flex flex-col gap-6 items-center text-center pb-8">
            <div className="w-[150px] h-[150px] mx-auto flex items-center justify-center">
              <svg width="150" height="150" viewBox="0 0 70 46" fill="none" xmlns="http://www.w3.org/2000/svg" className="animate-wave flex-shrink-0">
                <g clipPath="url(#clip0_8467_33285)">
                  <g clipPath="url(#clip1_8467_33285)">
                    <path d="M50.1451 23.724C48.7586 23.81 47.6384 24.1154 45.3368 28.0619C44.7644 29.0433 44.6481 29.749 44.238 30.6415C44.0574 29.3487 43.479 20.3053 45.4194 12.7533C46.0377 10.3486 44.7032 9.15665 43.4973 9.0084C42.169 8.84532 40.3356 8.94317 39.0685 13.797H39.0532L39.0716 13.6576C39.1787 11.4279 39.5888 8.62591 39.5888 8.62591C39.9592 5.93659 38.6921 5.57189 37.7647 5.4266C34.8815 5.308 32.9165 7.97952 32.537 16.6197H32.5309C32.3993 13.4916 32.7758 11.0009 32.7758 11.0009C33.1155 8.59626 32.3503 7.68302 31.5209 7.38948C29.6324 6.71937 28.7112 8.22859 28.2613 9.14479C26.988 11.7303 26.6483 14.9029 26.7095 17.7702L26.6911 17.7494C26.8166 15.0008 25.3077 13.0053 23.1285 14.3633C20.9493 15.7243 21.4972 20.7471 21.8644 23.7774C22.1032 25.7314 22.4215 27.6349 22.0848 29.921C20.8116 43.0681 29.611 44.9094 35.4814 44.9954C42.7291 45.3067 46.6345 41.5381 48.0914 38.1431C49.8482 34.0454 50.0686 31.8008 50.947 30.0781C52.0734 27.8632 52.8936 27.5875 52.964 26.013C53.0344 24.4386 51.5316 23.638 50.1543 23.721L50.1451 23.724Z" fill="#FFE165"/>
                    <path d="M53.0474 23.7441C52.3129 23.0473 51.208 22.6766 50.0847 22.7419C48.285 22.8516 47.0087 23.4891 45.0468 26.6024C44.9948 23.0413 45.1998 17.6953 46.4057 12.9927C46.8587 11.2256 46.4027 10.0722 45.9375 9.41688C45.3957 8.6519 44.554 8.14783 43.6236 8.03516C42.7758 7.93139 41.6678 7.92545 40.5874 8.78532C40.5874 8.77346 40.5905 8.75864 40.5905 8.75864C40.9394 6.2324 40.0395 4.78545 37.9185 4.4593L37.8022 4.44743C36.4953 4.3911 35.3751 4.80621 34.4722 5.67794C33.9886 6.14345 33.5692 6.74536 33.205 7.48959C32.798 6.9114 32.2746 6.61786 31.8614 6.46961C29.3363 5.57119 27.9407 7.49552 27.3346 8.72306C26.6307 10.1522 26.193 11.7534 25.9482 13.3871C25.8961 13.3545 25.8472 13.3219 25.7951 13.2922C25.2381 12.9809 24.0781 12.6014 22.5722 13.5413C20.0196 15.1365 20.344 19.7205 20.8521 23.8953C20.8797 24.1177 20.9072 24.3371 20.9348 24.5595C21.1521 26.2703 21.3571 27.8863 21.0756 29.7869L21.0694 29.8343C20.5583 35.1092 21.5836 39.1683 24.1179 41.9051C26.5542 44.5381 30.3708 45.9079 35.4301 45.9821C35.8005 45.9969 36.1616 46.0028 36.5136 45.9998C45.157 45.9227 48.2575 40.3039 49.0196 38.5249C50.0051 36.224 50.5162 34.5073 50.9233 33.1255C51.2386 32.0581 51.4895 31.216 51.8446 30.5163C52.2486 29.7216 52.6036 29.2057 52.9158 28.7491C53.4484 27.9722 53.9075 27.3021 53.9626 26.0568C54.0024 25.1554 53.684 24.3549 53.0382 23.7441H53.0474ZM35.9076 7.07152C36.3943 6.60304 36.9544 6.39548 37.6644 6.41031C38.2796 6.50815 38.8367 6.65344 38.5826 8.49178C38.5643 8.60742 38.1664 11.3679 38.0593 13.6154C38.0593 13.6302 38.0593 13.6451 38.0593 13.6599C37.4992 15.854 37.0309 19.0148 36.7799 23.6344C35.6934 23.6996 34.6099 23.8123 33.557 23.9605C33.2173 14.588 34.0039 8.90393 35.9045 7.07152H35.9076ZM29.1711 9.57106C29.9332 8.02923 30.5728 8.10632 31.1666 8.31684C31.9899 8.61038 31.8614 10.2026 31.7665 10.8638C31.7512 10.9706 31.3839 13.4523 31.5125 16.6101C31.4176 18.825 31.4298 21.3779 31.5431 24.2985C30.5361 24.4913 29.5812 24.7136 28.7089 24.9538C28.2957 23.6077 26.4685 15.0564 29.1711 9.57403V9.57106ZM51.2324 27.6609C50.9019 28.1413 50.4918 28.7402 50.0296 29.6475C49.5919 30.5044 49.3226 31.4236 48.9767 32.5829C48.5819 33.9142 48.0891 35.5717 47.1495 37.7688C46.4823 39.3225 43.6787 44.3691 35.4914 44.0132C30.9279 43.948 27.7019 42.8272 25.6298 40.5886C23.4935 38.2818 22.6396 34.7296 23.0895 30.0359C23.4017 27.8892 23.1721 26.0716 22.9487 24.3163C22.9211 24.0969 22.8936 23.8805 22.8661 23.661C22.6212 21.6359 21.9662 16.2543 23.671 15.1899C24.1301 14.9022 24.5066 14.837 24.7851 14.9912C25.2595 15.2551 25.737 16.2158 25.6696 17.7042C25.6666 17.7843 25.6758 17.8614 25.6911 17.9385C25.7768 21.4076 26.4164 24.426 26.7807 25.5587C26.1838 25.7751 25.6574 26.0005 25.2167 26.2258C24.7208 26.4808 24.5341 27.0738 24.7973 27.5542C24.981 27.8892 25.336 28.079 25.7033 28.076C25.8594 28.076 26.0186 28.0375 26.1685 27.9604C28.6446 26.6884 34.5181 25.3956 39.6937 25.535C40.2568 25.5439 40.719 25.1228 40.7343 24.5802C40.7496 24.0376 40.3089 23.5869 39.7488 23.5721C39.4396 23.5632 39.1274 23.5632 38.8153 23.5632C39.3325 14.247 40.7557 11.2078 41.8637 10.3094C42.3228 9.93873 42.7605 9.90908 43.3665 9.98321C43.5348 10.004 43.9572 10.0988 44.2602 10.5258C44.5877 10.9913 44.6489 11.6792 44.4347 12.5154C42.5615 19.8124 42.9839 28.3933 43.1982 30.4748C43.1614 30.5459 43.1278 30.6171 43.088 30.6912C42.6503 31.4888 41.8361 32.319 40.8659 32.2627C40.3119 32.236 39.8253 32.6452 39.7916 33.1848C39.7579 33.7274 40.1834 34.193 40.7435 34.2256C42.384 34.3205 43.9297 33.3449 44.8785 31.6163C44.9795 31.4325 45.0652 31.2575 45.1417 31.0885C45.1478 31.0767 45.1539 31.0618 45.16 31.05C45.3376 30.6645 45.4661 30.3117 45.5794 29.9944C45.7569 29.5022 45.9099 29.0753 46.216 28.5475C48.3891 24.8174 49.2705 24.7641 50.2041 24.7077C50.7519 24.6751 51.2967 24.8441 51.6181 25.1525C51.8476 25.3689 51.9486 25.6387 51.9333 25.9768C51.9027 26.6736 51.7038 26.9641 51.2233 27.6639L51.2324 27.6609Z" fill="black"/>
                  </g>
                </g>
                <defs>
                  <clipPath id="clip0_8467_33285">
                    <rect width="70" height="46" fill="white"/>
                  </clipPath>
                  <clipPath id="clip1_8467_33285">
                    <rect width="70" height="46" fill="white"/>
                  </clipPath>
                </defs>
              </svg>
            </div>
            <div className="flex items-center justify-center">
              <h1 className="heading">Let's Start Building!</h1>
            </div>
            <div className="flex flex-col items-center gap-2">
              <p className="text-sm max-w-[424px] text-content-secondary">
                OpenHands makes it easy to build and maintain software using AI-driven development.
              </p>
              <div className="bg-tertiary px-3 py-1 rounded-full">
                <p className="text-sm text-content-secondary">
                  Not sure how to start? <a href="https://docs.all-hands.dev/usage/getting-started" target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 text-content">Read this</a>
                </p>
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Existing Repository Container */}
            <div className="border border-border rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <GitBranch className="w-6 h-6 text-content" />
                <h2 className="text-xl leading-6 font-semibold text-content">Existing Repository</h2>
              </div>
              <RepoConnector
                onRepoSelection={(title) => setSelectedRepoTitle(title)}
              />
            </div>

            {/* Create New Project Container */}
            <div className="border border-border rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Plus className="w-6 h-6 text-content" />
                <h2 className="text-xl leading-6 font-semibold text-content">Create New Project</h2>
              </div>
              <div className="flex flex-col gap-4">
                <p className="text-sm text-content-secondary">
                  Start a new project from scratch or import from existing code.
                </p>
                <div className="flex flex-col gap-2">
                  <BrandButton
                    testId="header-launch-button"
                    variant="primary"
                    type="button"
                    onClick={() => createConversation({})}
                    isDisabled={isCreatingConversation}
                  >
                    {!isCreatingConversation && "Create New Project"}
                    {isCreatingConversation && t("HOME$LOADING")}
                  </BrandButton>
                  <a
                    href="/new-project"
                    className="text-sm text-content-secondary hover:text-content underline underline-offset-2 transition-colors"
                  >
                    Try Experimental UI →
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Projects Section */}
          <div className="mt-8">
            <h3 className="text-sm mb-3 font-medium text-content">Recent Projects</h3>
            <div className="text-sm text-content-secondary">
              <p className="mt-1">No recent projects found.</p>
              <p className="mt-1">Your recent projects will appear here once you start working on them.</p>
            </div>
          </div>

          {/* Recommended Tasks Section */}
          <div className="mt-6">
            <h3 className="text-sm mb-3 font-medium text-content">Recommended Tasks</h3>
            <div className="text-sm text-content-secondary">
              <p className="mt-1">No recommended tasks available.</p>
              <p className="mt-1">Tasks will be recommended based on your project activity and preferences.</p>
            </div>
          </div>

          {/* Task Suggestions - Full Width Below */}
          {providersAreSet && (
            <div className="mt-6 border border-border rounded-xl p-6 bg-base-secondary">
              <TaskSuggestions filterFor={selectedRepoTitle} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default HomeScreen;

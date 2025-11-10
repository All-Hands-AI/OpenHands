import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { GitRepository } from "#/types/git";

interface HomeState {
  recentRepositories: GitRepository[];
}

interface HomeActions {
  addRecentRepository: (repository: GitRepository) => void;
  clearRecentRepositories: () => void;
  getRecentRepositories: () => GitRepository[];
}

type HomeStore = HomeState & HomeActions;

const initialState: HomeState = {
  recentRepositories: [],
};

export const useHomeStore = create<HomeStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      addRecentRepository: (repository: GitRepository) =>
        set((state) => {
          // Remove the repository if it already exists to avoid duplicates
          const filteredRepos = state.recentRepositories.filter(
            (repo) => repo.id !== repository.id,
          );

          // Add the new repository to the beginning and keep only top 3
          const updatedRepos = [repository, ...filteredRepos].slice(0, 3);

          return {
            recentRepositories: updatedRepos,
          };
        }),

      clearRecentRepositories: () =>
        set(() => ({
          recentRepositories: [],
        })),

      getRecentRepositories: () => get().recentRepositories,
    }),
    {
      name: "home-store", // unique name for localStorage
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

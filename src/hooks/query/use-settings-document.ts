import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isNoBackend } from "#/api/backend-registry/active-store";
import SettingsService from "#/api/settings-service/settings-service.api";
import { useActiveBackend } from "#/contexts/active-backend-context";
import type { SettingsDocumentPatch } from "#/types/settings-document";
import { useIsAuthed } from "./use-is-authed";

const settingsDocumentKey = (
  backend: {
    id: string;
    kind: string;
    host: string;
    apiKey?: string | null;
  },
  orgId: string | null,
) => [
  "settings-document",
  backend.id,
  orgId,
  backend.kind,
  backend.host,
  backend.apiKey,
];

export const useSettingsDocument = () => {
  const { data: isAuthenticated } = useIsAuthed();
  const { backend, orgId } = useActiveBackend();
  return useQuery({
    queryKey: settingsDocumentKey(backend, orgId),
    queryFn: SettingsService.getSettingsDocument,
    enabled: !!isAuthenticated && !isNoBackend(backend),
    retry: false,
    refetchOnWindowFocus: false,
    meta: { disableToast: true },
  });
};

export const useSettingsDocumentSchema = () => {
  const { data: isAuthenticated } = useIsAuthed();
  const { backend, orgId } = useActiveBackend();
  return useQuery({
    queryKey: [...settingsDocumentKey(backend, orgId), "schema"],
    queryFn: SettingsService.getSettingsDocumentSchema,
    enabled: !!isAuthenticated && !isNoBackend(backend),
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 1000 * 60 * 5,
    meta: { disableToast: true },
  });
};

export const useSaveSettingsDocument = () => {
  const queryClient = useQueryClient();
  const { backend, orgId } = useActiveBackend();
  return useMutation({
    mutationFn: (patch: SettingsDocumentPatch) =>
      SettingsService.saveSettingsDocument(patch),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: settingsDocumentKey(backend, orgId),
      });
    },
    meta: { disableToast: true },
  });
};

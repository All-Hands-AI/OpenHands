import { 
  QueryClient, 
  UseMutationOptions, 
  UseMutationResult, 
  UseQueryOptions, 
  UseQueryResult, 
  useMutation, 
  useQuery 
} from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { queryClient } from '#/entry.client';

/**
 * Type for query options with default error type
 */
export type QueryOptions<TData, TError = AxiosError> = UseQueryOptions<
  TData,
  TError,
  TData,
  any
>;

/**
 * Type for mutation options with default error type
 */
export type MutationOptions<TData, TVariables, TError = AxiosError> = UseMutationOptions<
  TData,
  TError,
  TVariables,
  any
>;

/**
 * Enhanced useQuery hook with default error type
 */
export function useTypedQuery<TData, TError = AxiosError>(
  options: QueryOptions<TData, TError>
): UseQueryResult<TData, TError> {
  return useQuery<TData, TError, TData>(options);
}

/**
 * Enhanced useMutation hook with default error type
 */
export function useTypedMutation<TData, TVariables, TError = AxiosError>(
  options: MutationOptions<TData, TVariables, TError>
): UseMutationResult<TData, TError, TVariables, any> {
  return useMutation<TData, TError, TVariables>(options);
}

/**
 * Invalidate queries by key
 */
export function invalidateQueries(queryKey: unknown[]): Promise<void> {
  return queryClient.invalidateQueries({ queryKey });
}

/**
 * Set query data directly
 */
export function setQueryData<TData>(
  queryKey: unknown[],
  data: TData | ((oldData: TData | undefined) => TData)
): void {
  queryClient.setQueryData(queryKey, data);
}

/**
 * Get query data directly
 */
export function getQueryData<TData>(queryKey: unknown[]): TData | undefined {
  return queryClient.getQueryData<TData>(queryKey);
}

/**
 * Prefetch query data
 */
export function prefetchQuery<TData>(
  queryKey: unknown[],
  queryFn: () => Promise<TData>,
  options?: { staleTime?: number; cacheTime?: number }
): Promise<void> {
  return queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime: options?.staleTime,
    gcTime: options?.cacheTime,
  });
}

/**
 * Reset the query client (useful for logout)
 */
export function resetQueryClient(): void {
  queryClient.clear();
}

/**
 * Get the query client instance
 */
export function getQueryClient(): QueryClient {
  return queryClient;
}
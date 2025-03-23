import { apiService } from '../api-service';
import { SaveFileSuccessResponse, FileUploadSuccessResponse } from '../open-hands.types';

interface ListFilesParams {
  conversationId: string;
  path?: string;
}

interface GetFileParams {
  conversationId: string;
  path: string;
}

interface SaveFileParams {
  conversationId: string;
  path: string;
  content: string;
}

interface UploadFilesParams {
  conversationId: string;
  files: File[];
}

export const filesApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    listFiles: builder.query<string[], ListFilesParams>({
      query: ({ conversationId, path }) => ({
        url: `/api/conversations/${conversationId}/list-files`,
        method: 'GET',
        params: { path },
      }),
      providesTags: (result, error, { conversationId, path }) => [
        { type: 'Files', id: `${conversationId}:${path || 'root'}` },
      ],
    }),
    getFile: builder.query<string, GetFileParams>({
      query: ({ conversationId, path }) => ({
        url: `/api/conversations/${conversationId}/select-file`,
        method: 'GET',
        params: { file: path },
      }),
      transformResponse: (response: { code: string }) => response.code,
      providesTags: (result, error, { conversationId, path }) => [
        { type: 'File', id: `${conversationId}:${path}` },
      ],
    }),
    saveFile: builder.mutation<SaveFileSuccessResponse, SaveFileParams>({
      query: ({ conversationId, path, content }) => ({
        url: `/api/conversations/${conversationId}/save-file`,
        method: 'POST',
        data: {
          filePath: path,
          content,
        },
      }),
      invalidatesTags: (result, error, { conversationId, path }) => [
        { type: 'File', id: `${conversationId}:${path}` },
        { type: 'Files', id: `${conversationId}:${path.split('/').slice(0, -1).join('/') || 'root'}` },
      ],
    }),
    uploadFiles: builder.mutation<FileUploadSuccessResponse, UploadFilesParams>({
      query: ({ conversationId, files }) => {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));
        
        return {
          url: `/api/conversations/${conversationId}/upload-files`,
          method: 'POST',
          data: formData,
        };
      },
      invalidatesTags: (result, error, { conversationId }) => [
        { type: 'Files', id: `${conversationId}:root` },
      ],
    }),
    getWorkspaceZip: builder.query<Blob, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}/zip-directory`,
        method: 'GET',
        responseType: 'blob',
      }),
    }),
  }),
});

export const {
  useListFilesQuery,
  useGetFileQuery,
  useSaveFileMutation,
  useUploadFilesMutation,
  useGetWorkspaceZipQuery,
} = filesApiSlice;
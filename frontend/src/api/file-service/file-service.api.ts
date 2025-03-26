import { AxiosInstance } from "axios";
import { openHands } from "../open-hands-axios";
import { GetFilesResponse, GetFileResponse } from "./file-service.types";
import { getConversationUrl } from "./file-service.utils";

class FileService {
  constructor(private axiosInstance: AxiosInstance = openHands) {}

  /**
   * Retrieve the list of files available in the workspace
   * @param conversationId ID of the conversation
   * @param path Path to list files from. If provided, it lists all the files in the given path
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  async getFiles(
    conversationId: string,
    path?: string,
  ): Promise<GetFilesResponse> {
    const url = `${getConversationUrl(conversationId)}/list-files`;
    const { data } = await this.axiosInstance.get<GetFilesResponse>(url, {
      params: { path },
    });

    return data;
  }

  /**
   * Retrieve the content of a file
   * @param conversationId ID of the conversation
   * @param path Full path of the file to retrieve
   * @returns Code content of the file
   */
  async getFile(conversationId: string, path: string): Promise<string> {
    const url = `${getConversationUrl(conversationId)}/select-file`;
    const { data } = await this.axiosInstance.get<GetFileResponse>(url, {
      params: { file: path },
    });

    return data.code;
  }
}

export const fileService = new FileService();

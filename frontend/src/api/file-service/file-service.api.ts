import { openHands } from "../open-hands-axios";
import { GetFilesResponse, GetFileResponse } from "./file-service.types";
import { getConversationUrl } from "../conversation.utils";

export class FileService {
  /**
   * Retrieve the list of files available in the workspace
   * @param conversationId ID of the conversation
   * @param path Path to list files from. If provided, it lists all the files in the given path
   * @returns List of files available in the given path. If path is not provided, it lists all the files in the workspace
   */
  static async getFiles(
    conversationId: string,
    path?: string,
  ): Promise<GetFilesResponse> {
    const url = `${getConversationUrl(conversationId)}/list-files`;
    const { data } = await openHands.get<GetFilesResponse>(url, {
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
  static async getFile(conversationId: string, path: string): Promise<string> {
    const url = `${getConversationUrl(conversationId)}/select-file`;
    const { data } = await openHands.get<GetFileResponse>(url, {
      params: { file: path },
    });

    return data.code;
  }
}

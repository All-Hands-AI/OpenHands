import { useUploadFilesMutation } from '../api/slices';
import { useConversation } from '../context/conversation-context';

export const useUploadFiles = () => {
  const { conversationId } = useConversation();
  const [uploadFilesMutation] = useUploadFilesMutation();

  const uploadFiles = (files: File[]) => {
    return uploadFilesMutation({ conversationId, files });
  };

  return { uploadFiles };
};
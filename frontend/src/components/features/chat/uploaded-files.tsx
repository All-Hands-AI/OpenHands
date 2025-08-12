import { useSelector, useDispatch } from "react-redux";
import { RootState } from "#/store";
import { UploadedFile } from "./uploaded-file";
import { UploadedImage } from "./uploaded-image";
import { removeFile, removeImage } from "#/state/conversation-slice";

export function UploadedFiles() {
  const dispatch = useDispatch();
  const images = useSelector((state: RootState) => state.conversation.images);
  const files = useSelector((state: RootState) => state.conversation.files);
  const loadingFiles = useSelector(
    (state: RootState) => state.conversation.loadingFiles,
  );
  const loadingImages = useSelector(
    (state: RootState) => state.conversation.loadingImages,
  );

  const handleRemoveFile = (index: number) => {
    dispatch(removeFile(index));
  };

  const handleRemoveImage = (index: number) => {
    dispatch(removeImage(index));
  };

  // Don't render anything if there are no files, images, or loading items
  if (
    images.length === 0 &&
    files.length === 0 &&
    loadingFiles.length === 0 &&
    loadingImages.length === 0
  ) {
    return null;
  }

  return (
    <div className="flex items-center gap-4 w-full overflow-x-auto pb-4 custom-scrollbar">
      {/* Regular files */}
      {files.map((file, index) => (
        <UploadedFile
          key={`file-${index}-${file.name}`}
          file={file}
          onRemove={() => handleRemoveFile(index)}
          isLoading={loadingFiles.includes(file.name)}
        />
      ))}

      {/* Loading files (files currently being processed) */}
      {loadingFiles.map((fileName, index) => {
        // Create a temporary File object for display purposes
        const tempFile = new File([], fileName);
        return (
          <UploadedFile
            key={`loading-file-${index}-${fileName}`}
            file={tempFile}
            onRemove={() => {}} // No remove action during loading
            isLoading
          />
        );
      })}

      {/* Regular images */}
      {images.map((image, index) => (
        <UploadedImage
          key={`image-${index}-${image.name}`}
          image={image}
          onRemove={() => handleRemoveImage(index)}
          isLoading={loadingImages.includes(image.name)}
        />
      ))}

      {/* Loading images (images currently being processed) */}
      {loadingImages.map((imageName, index) => {
        // Create a temporary File object for display purposes
        const tempImage = new File([], imageName);
        return (
          <UploadedImage
            key={`loading-image-${index}-${imageName}`}
            image={tempImage}
            onRemove={() => {}} // No remove action during loading
            isLoading
          />
        );
      })}
    </div>
  );
}

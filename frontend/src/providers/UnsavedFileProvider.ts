// import { listUnsavedFileNames } from "#/services/unsavedFileContentService";
import { createContext /* , useEffect, useState */ } from "react";

export const UnsavedFileProviderContext = createContext<string[]>([]);

export interface UnsavedFileProviderProperties {
  children: JSX.Element | JSX.Element[];
}

/*
export const UnsavedFileProvider = ({ children }: UnsavedFileProviderProperties) => {
    const [unsavedFiles, setUnsavedFiles] = useState([])
    useEffect(() => {
        listUnsavedFileNames().then(setUnsavedFiles);
    })

    return (
        <UnsavedFileProviderContext.Provider value={unsavedFiles}>
            {children}
        </UnsavedFileProviderContext.Provider>
    );
  };

  export const useUnsavedFiles = () => {
    // Hack to force type checker to accept the type of the context
    const openApi: OpenApi = useContext(OpenApiContext);
    return openApi;
  };
  */

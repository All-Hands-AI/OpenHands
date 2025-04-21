declare module 'swagger-ui-react' {
  import React from 'react';

  interface SwaggerUIProps {
    spec?: object;
    url?: string;
    layout?: string;
    docExpansion?: 'list' | 'full' | 'none';
    defaultModelsExpandDepth?: number;
    defaultModelExpandDepth?: number;
    showExtensions?: boolean;
    showCommonExtensions?: boolean;
    supportedSubmitMethods?: Array<string>;
    onComplete?: () => void;
    requestInterceptor?: (req: any) => any;
    responseInterceptor?: (res: any) => any;
    showMutatedRequest?: boolean;
    deepLinking?: boolean;
    presets?: Array<any>;
    plugins?: Array<any>;
    initialState?: object;
    filter?: boolean | string | ((path: string, method: string) => boolean);
    validatorUrl?: string | null;
    withCredentials?: boolean;
    oauth2RedirectUrl?: string;
    tagsSorter?: (a: string, b: string) => number;
    operationsSorter?: (a: object, b: object) => number;
  }

  const SwaggerUI: React.FC<SwaggerUIProps>;

  export default SwaggerUI;
}
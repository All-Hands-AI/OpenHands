import { ClientActionFunctionArgs, json } from "@remix-run/react";
import { setImportedProjectZip } from "#/state/initial-query-slice";
import store from "#/store";

const convertZipToBase64 = async (file: File) => {
  const reader = new FileReader();

  return new Promise<string>((resolve) => {
    reader.onload = () => {
      resolve(reader.result as string);
    };
    reader.readAsDataURL(file);
  });
};

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const isMultipart = !!request.headers
    .get("Content-Type")
    ?.includes("multipart");

  if (isMultipart) {
    const formData = await request.formData();
    const importedProject = formData.get("imported-project");

    if (importedProject instanceof File) {
      store.dispatch(
        setImportedProjectZip(await convertZipToBase64(importedProject)),
      );
    }
  }

  return json(null);
};

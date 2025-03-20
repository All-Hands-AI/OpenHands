import React from "react";
import PlusIcon from "#/icons/plus.svg?react";
import XMarkIcon from "#/icons/x-mark.svg?react";
import { SettingsInput } from "./settings-input";

interface SecretEntry {
  id: string;
  name: string;
  value: string;
}

export function CustomSecrets() {
  const [secrets, setSecrets] = React.useState<SecretEntry[]>([]);

  const addNewSecret = () => {
    const newSecret = {
      id: crypto.randomUUID(),
      name: "",
      value: "",
    };
    setSecrets([...secrets, newSecret]);
  };

  const removeSecret = (id: string) => {
    setSecrets(secrets.filter((secret) => secret.id !== id));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Custom Secrets</h3>
        <button
          type="button"
          onClick={addNewSecret}
          className="flex items-center gap-1 text-sm text-primary hover:text-primary/80"
        >
          <PlusIcon className="h-4 w-4" />
          Add Secret
        </button>
      </div>

      {secrets.map((secret) => (
        <div key={secret.id} className="flex items-start gap-2">
          <SettingsInput
            name={`secret-name-${secret.id}`}
            placeholder="Secret Name"
            className="w-[330px]"
          />
          <SettingsInput
            name={`secret-value-${secret.id}`}
            type="password"
            placeholder="Secret Value"
            className="w-[330px]"
          />
          <button
            type="button"
            onClick={() => removeSecret(secret.id)}
            className="mt-2 p-1 text-gray-400 hover:text-gray-300"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      ))}
    </div>
  );
}

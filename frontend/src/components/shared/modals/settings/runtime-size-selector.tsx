import React from 'react';
import { useTranslation } from 'react-i18next';

interface RuntimeSizeSelectorProps {
  isDisabled: boolean;
  defaultValue?: number;
}

export function RuntimeSizeSelector({ isDisabled, defaultValue }: RuntimeSizeSelectorProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="runtime-size" className="text-sm font-medium text-gray-700">
        {t('Runtime Size')}
      </label>
      <select
        id="runtime-size"
        name="runtime-size"
        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        defaultValue={defaultValue || 1}
        disabled={isDisabled}
      >
        <option value={1}>{t('1x (2 core, 8G)')}</option>
        <option value={2}>{t('2x (4 core, 16G)')}</option>
      </select>
    </div>
  );
}

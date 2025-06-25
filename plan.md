
# Plan to Add Temperature Setting to LLM Settings Menu

## 1. Explore the Current LLM Settings Menu
- **File**: `frontend/src/routes/llm-settings.tsx`
- **Purpose**: Understand the current structure and components used in the LLM settings menu.
- **Actions**:
  - Identify the existing settings and their components.
  - Determine where new settings can be added without disrupting the existing functionality.

## 2. Add Temperature Setting to the Settings Type
- **File**: `frontend/src/types/settings.ts`
- **Purpose**: Define the new temperature setting in the settings type.
- **Actions**:
  - Add a new field `temperature` to the `Settings` and `ApiSettings` types.
  - Provide a default value for the temperature setting in `DEFAULT_SETTINGS`.

## 3. Update the Settings Hooks
- **Files**:
  - `frontend/src/hooks/query/use-settings.ts`
  - `frontend/src/hooks/mutation/use-save-settings.ts`
- **Purpose**: Ensure the new temperature setting is included in the settings hooks.
- **Actions**:
  - Update `useSettings` to map the temperature setting from the API response.
  - Update `useSaveSettings` to include the temperature setting in API requests.

## 4. Add UI Components for Temperature Setting
- **File**: `frontend/src/routes/llm-settings.tsx`
- **Purpose**: Add UI components to display and edit the temperature setting.
- **Actions**:
  - Add a new input field for the temperature setting.
  - Ensure the input field is properly bound to the state and can be edited by the user.

## 5. Update i18n Translations
- **Files**:
  - `frontend/src/i18n/translation.json`
  - `frontend/src/i18n/declaration.ts`
- **Purpose**: Add translations for the new temperature setting.
- **Actions**:
  - Add a new translation key for the temperature setting label and any associated tooltips.
  - Update the declaration file to include the new translation key.

## 6. Update Backend to Support Temperature Setting
- **File**: `openhands/storage/data_models/settings.py`
- **Purpose**: Ensure the backend can handle the new temperature setting.
- **Actions**:
  - Add the temperature setting to the `Settings` model.
  - Update any relevant backend code to apply the temperature setting.

## 7. Test the New Temperature Setting
- **Purpose**: Verify that the new temperature setting works as expected.
- **Actions**:
  - Run the application and navigate to the LLM settings menu.
  - Verify that the temperature setting is displayed and can be edited.
  - Ensure that the setting is saved correctly and applied in subsequent sessions.

## 8. Document the Changes
- **File**: `README.md`
- **Purpose**: Document the new temperature setting in the project documentation.
- **Actions**:
  - Add a section describing the new temperature setting and its purpose.
  - Provide instructions on how to use the new setting.

import React from "react";
import BaseModal from "../BaseModal";
import SettingsForm from "./SettingsForm";

interface SettingsProps {
  isOpen: boolean;
}

const Settings: React.FC<SettingsProps> = ({ isOpen }) => (
  <BaseModal isOpen={isOpen} title="Settings">
    <SettingsForm />
  </BaseModal>
);

export default Settings;

import { StylesConfig } from "react-select";

export interface SelectOptionBase {
  value: string;
  label: string;
}

export const getCustomStyles = <T extends SelectOptionBase>(): StylesConfig<
  T,
  false
> => ({
  control: (provided, state) => ({
    ...provided,
    backgroundColor: state.isDisabled ? "#363636" : "#454545", // darker tertiary when disabled
    border: "1px solid #717888",
    borderRadius: "0.125rem",
    minHeight: "2.5rem",
    padding: "0 0.5rem",
    boxShadow: state.isFocused ? "0 0 0 1px #717888" : "none",
    opacity: state.isDisabled ? 0.6 : 1,
    cursor: state.isDisabled ? "not-allowed" : "pointer",
    "&:hover": {
      borderColor: "#717888",
    },
  }),
  input: (provided) => ({
    ...provided,
    color: "#ECEDEE", // content
  }),
  placeholder: (provided) => ({
    ...provided,
    fontStyle: "italic",
    color: "#B7BDC2", // tertiary-light
  }),
  singleValue: (provided, state) => ({
    ...provided,
    color: state.isDisabled ? "#B7BDC2" : "#ECEDEE", // tertiary-light when disabled, content otherwise
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: "#454545", // tertiary
    border: "1px solid #717888",
    borderRadius: "0.75rem",
    overflow: "hidden", // ensure menu items don't overflow rounded corners
  }),
  menuList: (provided) => ({
    ...provided,
    padding: "0.25rem", // add some padding around menu items
  }),
  option: (provided, state) => {
    let backgroundColor = "transparent";
    if (state.isSelected) {
      backgroundColor = "#C9B974"; // primary for selected
    } else if (state.isFocused) {
      backgroundColor = "#24272E"; // base-secondary for hover/focus
    }

    return {
      ...provided,
      backgroundColor,
      color: state.isSelected ? "#000000" : "#ECEDEE", // black text on yellow, white on gray
      borderRadius: "0.5rem", // rounded menu items
      margin: "0.125rem 0", // small gap between items
      "&:hover": {
        backgroundColor: state.isSelected ? "#C9B974" : "#24272E", // keep yellow if selected, else gray
        color: state.isSelected ? "#000000" : "#ECEDEE", // maintain text color on hover
      },
      "&:active": {
        backgroundColor: state.isSelected ? "#C9B974" : "#24272E",
        color: state.isSelected ? "#000000" : "#ECEDEE",
      },
    };
  },
  clearIndicator: (provided) => ({
    ...provided,
    color: "#B7BDC2", // tertiary-light
    "&:hover": {
      color: "#ECEDEE", // content
    },
  }),
  dropdownIndicator: (provided) => ({
    ...provided,
    color: "#B7BDC2", // tertiary-light
    "&:hover": {
      color: "#ECEDEE", // content
    },
  }),
  loadingIndicator: (provided) => ({
    ...provided,
    color: "#B7BDC2", // tertiary-light
  }),
});

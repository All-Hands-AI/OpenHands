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
  }),
  option: (provided, state) => {
    let backgroundColor = "transparent";
    if (state.isSelected) {
      backgroundColor = "#C9B974"; // primary
    } else if (state.isFocused) {
      backgroundColor = "#24272E"; // base-secondary
    }

    return {
      ...provided,
      backgroundColor,
      color: "#ECEDEE", // content
      "&:hover": {
        backgroundColor: "#24272E", // base-secondary
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

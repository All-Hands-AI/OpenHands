import { StylesConfig } from "react-select";

export interface SelectOptionBase {
  value: string;
  label: string;
}

export type SelectOption = SelectOptionBase;

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

// Custom styles for the repo-selection-form dropdowns.
export const providerDropdownStyles: StylesConfig<SelectOption, false> = {
  control: (provided) => ({
    ...provided,
    maxWidth: "124px",
    height: "1.5rem",
    minHeight: "1.5rem",
    maxHeight: "1.5rem",
    padding: "0",
    border: "1px solid #727987",
    backgroundColor: "#454545",
    borderRadius: "0.25rem",
    boxShadow: "none",
    paddingLeft: "0.375rem",
    "> div:first-child": {
      transform: "translateY(-1px)",
    },
    "&:hover": {
      borderColor: "#727987",
    },
    "& .provider-dropdown__single-value": {
      color: "#A3A3A3",
      fontSize: "0.75rem",
      fontWeight: "400",
      lineHeight: "1.25rem",
    },
    "& .provider-dropdown__value-container": {
      height: "1.5rem",
      padding: "0 0.5rem",
      transform: "translateY(-1px)",
      paddingLeft: "0.125rem",
    },
    "& .provider-dropdown__indicators-container": {
      height: "1.5rem",
      padding: "0 0.5rem",
      "& > div": {
        padding: "0",
      },
    },
    "& .provider-dropdown__indicators": {
      transform: "translateY(-1px)",
      height: "1.5rem",
      padding: "0 0.5rem",
      "& > div": {
        padding: "0",
      },
    },
    "& .provider-dropdown__dropdown-indicator": {
      color: "#fff",
      "&:hover": {
        color: "#fff",
      },
    },
  }),
  menu: (provided) => ({
    ...provided,
    borderRadius: "0.4375rem",
    boxShadow: "none",
    border: "1px solid #727987",
    marginTop: "0.25rem",
    "& .provider-dropdown__menu-list": {
      background: "#454545",
      borderRadius: "0.375rem",
      padding: "0.25rem",
    },
    "& .provider-dropdown__option": {
      color: "#fff",
      fontSize: "0.75rem",
      fontWeight: "400",
      background: "transparent",
      borderRadius: "0.375rem",
      padding: "0 0.5rem",
      height: "1.5rem",
      display: "flex",
      alignItems: "center",
      "&:hover": {
        cursor: "pointer",
        backgroundColor: "#5C5D62",
      },
    },
  }),
};

export const repoBranchDropdownStyles: StylesConfig<SelectOption, false> = {
  control: (provided) => ({
    ...provided,
    maxWidth: "auto",
    minHeight: "42px",
    maxHeight: "42px",
    border: "1px solid #727987",
    backgroundColor: "#454545",
    borderRadius: "0.25rem",
    boxShadow: "none",
    padding: "0 0.75rem",
    height: "42px",
    "> div:first-child": {
      transform: "translateY(-1px)",
    },
    "&:hover": {
      borderColor: "#727987",
    },
    "& .repo-branch-dropdown__single-value": {
      color: "#A3A3A3",
      fontSize: "0.875rem",
      fontWeight: "400",
      lineHeight: "1.25rem",
    },
    "& .repo-branch-dropdown__value-container": {
      height: "42px",
      padding: "0 0.5rem",
      transform: "translateY(-1px)",
      paddingLeft: "0.25rem",
    },
    "& .repo-branch-dropdown__indicators-container": {
      height: "42px",
      padding: "0 0.5rem",
      "& > div": {
        padding: "0",
      },
    },
    "& .repo-branch-dropdown__indicators": {
      transform: "translateY(-1px)",
      height: "42px",
      padding: "0 0.5rem",
      "& > div": {
        padding: "0",
      },
    },
    "& .repo-branch-dropdown__dropdown-indicator": {
      color: "#fff",
      "&:hover": {
        color: "#fff",
      },
    },
  }),
  menu: (provided) => ({
    ...provided,
    borderRadius: "0.4375rem",
    boxShadow: "none",
    border: "1px solid #727987",
    marginTop: "0.25rem",
    "& .repo-branch-dropdown__menu-list": {
      background: "#454545",
      borderRadius: "0.375rem",
      padding: "0.375rem 0.25rem",
      /* WebKit browsers (Chrome, Safari, Edge) */
      "&::-webkit-scrollbar": {
        width: "6px",
        height: "6px",
      },

      "&::-webkit-scrollbar-track": {
        background: "transparent",
      },

      "&::-webkit-scrollbar-thumb": {
        background: "rgba(208, 217, 250, 0.3)",
        borderRadius: "3px",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      },

      /* Firefox */
      "&": {
        scrollbarWidth: "thin",
        scrollbarColor: "rgba(208, 217, 250, 0.3) transparent",
      },
    },
    "& .repo-branch-dropdown__option": {
      color: "#fff",
      fontSize: "0.875rem",
      fontWeight: "400",
      background: "transparent",
      borderRadius: "0.375rem",
      padding: "0.5rem",
      display: "flex",
      alignItems: "center",
      "&:hover": {
        cursor: "pointer",
        backgroundColor: "#5C5D62",
      },
    },
  }),
};

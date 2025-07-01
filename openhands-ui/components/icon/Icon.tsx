import * as icons from "react-bootstrap-icons";

export type IconProps = Omit<icons.IconProps, "name"> & {
  icon: keyof typeof icons;
};

export const Icon = ({ icon, ...props }: IconProps) => {
  const BootstrapIcon = icons[icon];

  return <BootstrapIcon {...props} />;
};

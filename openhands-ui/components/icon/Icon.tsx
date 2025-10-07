import * as icons from "react-bootstrap-icons";

export type IconProps = icons.IconProps & {
  icon: keyof typeof icons;
};

export const Icon = ({ icon, ...props }: IconProps) => {
  const BootstrapIcon = icons[icon];

  return <BootstrapIcon {...props} />;
};

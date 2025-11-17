import { type PlaceholderProps } from "react-select";
import { Typography } from "../../typography/Typography";
import { cn } from "../../../shared/utils/cn";

export const Placeholder = ({
  innerProps,
  children,
  selectProps: {
    customProps: { error },
  },
}: PlaceholderProps) => {
  return (
    <Typography.Text
      {...innerProps}
      fontSize="m"
      fontWeight={400}
      style={{
        gridArea: "1 / 1 / 2 / 3",
      }}
      className={cn(
        innerProps.className,
        "text-light-neutral-300",
        error && "text-red-400"
      )}
    >
      {children}
    </Typography.Text>
  );
};

import { Typography } from "../../typography/Typography";
import { cn } from "../../../shared/utils/cn";
import type { SingleValueProps } from "react-select";

export const SingleValue = ({
  innerProps,
  selectProps: {
    customProps: { error },
  },
  children,
}: SingleValueProps) => {
  return (
    <Typography.Text
      {...innerProps}
      fontSize="m"
      fontWeight={400}
      style={{
        gridArea: "1 / 1 / 2 / 3",
      }}
      className={cn("text-white", error && "text-red-400")}
    >
      {children}
    </Typography.Text>
  );
};

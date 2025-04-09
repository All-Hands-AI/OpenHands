import { rocketDarkImg, rocketLightImg } from ".";
import { useTheme } from "#/components/layout/theme-provider";
import { cn } from "#/utils/utils";

interface RocketImageProps {
  className?: string;
}

const RocketImage = ({ className }: RocketImageProps) => {
  const { theme } = useTheme();

  return theme === "light" ? (
    <img
      src={rocketLightImg}
      alt="rocket"
      className={cn("w-[156px] h-[156px]", className)}
    />
  ) : (
    <img
      src={rocketDarkImg}
      alt="rocket"
      className={cn("w-[156px] h-[156px]", className)}
    />
  );
};

export default RocketImage;

import { rocketDarkImg, rocketLightImg } from "."
import { useTheme } from "#/components/layout/theme-provider"
import { cn } from "#/utils/utils"

interface RocketImageProps {
  className?: string
}

const RocketImage = ({ className }: RocketImageProps) => {
  const { theme } = useTheme()

  return (
    <img
      src={theme === "light" ? rocketLightImg : rocketDarkImg}
      alt="rocket"
      className={cn("h-[156px] w-[156px]", className)}
    />
  )
}

export default RocketImage

import React from "react";
import { ChevronLeft } from "#/assets/chevron-left";
import { ChevronRight } from "#/assets/chevron-right";
import { ImagePreview } from "./image-preview";
import { cn } from "#/utils/utils";

type ImageFile = { src: string; id?: string };

interface ImageCarouselProps {
  size: "small" | "large";
  images: ImageFile[];
  onRemove?: (id: string) => void;
}

export function ImageCarousel({
  size = "small",
  images,
  onRemove,
}: ImageCarouselProps) {
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);
  const [isScrollable, setIsScrollable] = React.useState(false);
  const [isAtStart, setIsAtStart] = React.useState(true);
  const [isAtEnd, setIsAtEnd] = React.useState(false);

  React.useEffect(() => {
    const scrollContainer = scrollContainerRef.current;

    if (scrollContainer) {
      const hasScroll =
        scrollContainer.scrollWidth > scrollContainer.clientWidth;
      setIsScrollable(hasScroll);
    }
  }, [images]);

  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const scrollContainer = event.currentTarget;
    setIsAtStart(scrollContainer.scrollLeft === 0);
    setIsAtEnd(
      scrollContainer.scrollLeft + scrollContainer.clientWidth ===
        scrollContainer.scrollWidth,
    );
  };

  return (
    <div data-testid="image-carousel" className="relative">
      {isScrollable && (
        <div className="absolute right-full transform top-1/2 -translate-y-1/2">
          <ChevronLeft active={!isAtStart} />
        </div>
      )}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className={cn(
          "flex overflow-x-auto",
          size === "small" && "gap-2",
          size === "large" && "gap-4",
        )}
      >
        {images.map((image) => (
          <ImagePreview
            key={image.id}
            size={size}
            src={image.src}
            onRemove={() => onRemove?.(image.id!)}
          />
        ))}
      </div>
      {isScrollable && (
        <div className="absolute left-full transform top-1/2 -translate-y-1/2">
          <ChevronRight active={!isAtEnd} />
        </div>
      )}
    </div>
  );
}

import React from "react";
import { Popover, PopoverTrigger, PopoverContent } from "@heroui/react";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import AllHandsLogoWhite from "#/assets/branding/all-hands-logo-white.svg?react";
import { cn } from "#/utils/utils";
import { useTheme } from "#/context/theme-context";

interface LogoPopoverButtonProps {
  className?: string;
}

interface PopoverCardProps {
  title: string;
  description: string;
  href: string;
  imageUrl: string;
}

function PopoverCard({ title, description, href, imageUrl }: PopoverCardProps) {
  const { theme } = useTheme();

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "block p-3 rounded-lg transition-colors duration-150 group min-w-[200px]",
        theme === "dark"
          ? "hover:bg-neutral-900"
          : "hover:bg-gray-100"
      )}
    >
      <div className="flex flex-col gap-3">
        <div className="w-full h-24 rounded-md overflow-hidden bg-gray-700 flex items-center justify-center">
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to a placeholder if image fails to load
              e.currentTarget.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%23F3CE49'/%3E%3Ctext x='50' y='50' font-family='Arial' font-size='12' fill='black' text-anchor='middle' dy='.3em'%3E" + title + "%3C/text%3E%3C/svg%3E";
            }}
          />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm text-content group-hover:text-content transition-colors duration-150">
            {title}
          </h3>
          <p className="text-xs text-content-secondary mt-1 leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </a>
  );
}

export function LogoPopoverButton({ className }: LogoPopoverButtonProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const closeTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const { theme } = useTheme();

  const handleMouseEnter = () => {
    // Clear any pending close timeout
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    // Set a delay before closing to allow mouse to move to popover
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 150); // 150ms delay is standard practice
  };

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
      }
    };
  }, []);

  const cards: PopoverCardProps[] = [
    {
      title: "About AllHands",
      description: "Learn about our mission to democratize AI-powered software development and our journey so far.",
      href: "https://all-hands.dev",
      imageUrl: "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=200&h=100&fit=crop&crop=center",
    },
    {
      title: "Community",
      description: "Join thousands of developers in our Slack and Discord communities. Share ideas, get help, and contribute.",
      href: "https://join.slack.com/t/openhands-ai/shared_invite/zt-34zm4j0gj-Qz5kRHoca8DFCbqXPS~f_A",
      imageUrl: "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=200&h=100&fit=crop&crop=center",
    },
    {
      title: "Join Team",
      description: "We're hiring! Join our team of engineers, researchers, and designers building the future of AI development.",
      href: "https://all-hands.dev/careers",
      imageUrl: "https://images.unsplash.com/photo-1552664730-d307ca884978?w=200&h=100&fit=crop&crop=center",
    },
    {
      title: "Learning Center",
      description: "Explore tutorials, guides, and resources to master AI-powered development with OpenHands.",
      href: "https://docs.all-hands.dev",
      imageUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=100&fit=crop&crop=center",
    },
  ];

  return (
    <Popover
      isOpen={isOpen}
      onOpenChange={setIsOpen}
      placement="bottom-start"
      showArrow={false}
    >
      <PopoverTrigger>
        <button
          type="button"
          aria-label="AllHands Logo Menu"
          className={cn(
            "relative group transition-all duration-300",
            className
          )}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="relative">
            {theme === "dark" ? (
              <AllHandsLogoWhite
                width={34}
                height={34}
                className={cn(
                  "transition-all duration-300",
                  isOpen && "animate-logo-jump"
                )}
              />
            ) : (
              <AllHandsLogo
                width={34}
                height={34}
                className={cn(
                  "transition-all duration-300",
                  isOpen && "animate-logo-jump"
                )}
              />
            )}
          </div>
        </button>
      </PopoverTrigger>

      <PopoverContent
        className="w-auto max-w-4xl p-4 bg-base border border-border rounded-xl shadow-xl"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="flex gap-3 overflow-x-auto pb-2">
          {cards.map((card, index) => (
            <PopoverCard
              key={index}
              title={card.title}
              description={card.description}
              href={card.href}
              imageUrl={card.imageUrl}
            />
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

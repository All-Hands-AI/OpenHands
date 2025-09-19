import { useState } from "react";
import { MobileHeader } from "./mobile-header";
import { SettingsNavigation } from "./settings-navigation";

interface NavigationItem {
  to: string;
  icon: React.ReactNode;
  text: string;
}

interface SettingsLayoutProps {
  children: React.ReactNode;
  navigationItems: NavigationItem[];
  isSaas: boolean;
}

export function SettingsLayout({
  children,
  navigationItems,
  isSaas,
}: SettingsLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="flex flex-col h-full px-[14px] pt-8">
      {/* Mobile header */}
      <MobileHeader
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMenu={toggleMobileMenu}
      />

      {/* Desktop layout with navigation and main content */}
      <div className="flex flex-1 overflow-hidden gap-10">
        {/* Navigation */}
        <SettingsNavigation
          isMobileMenuOpen={isMobileMenuOpen}
          onCloseMobileMenu={closeMobileMenu}
          navigationItems={navigationItems}
          isSaas={isSaas}
        />

        {/* Main content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

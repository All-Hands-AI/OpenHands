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
    <div className="flex flex-col md:flex-row h-full">
      {/* Mobile header */}
      <MobileHeader
        isMobileMenuOpen={isMobileMenuOpen}
        onToggleMenu={toggleMobileMenu}
      />

      {/* Navigation */}
      <SettingsNavigation
        isMobileMenuOpen={isMobileMenuOpen}
        onCloseMobileMenu={closeMobileMenu}
        navigationItems={navigationItems}
        isSaas={isSaas}
      />

      {/* Main content */}
      <main className="flex-1 px-3 sm:px-[14px] md:px-6 lg:px-8 py-4 md:py-6 overflow-auto">
        {children}
      </main>
    </div>
  );
}

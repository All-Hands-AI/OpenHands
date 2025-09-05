import { ComponentType } from "react";
import { TabWrapper } from "./tab-wrapper";

interface TabContentProps {
  isActive: boolean;
  component: ComponentType;
}

export function TabContent({
  isActive,
  component: Component,
}: TabContentProps) {
  return (
    <TabWrapper isActive={isActive}>
      <Component />
    </TabWrapper>
  );
}

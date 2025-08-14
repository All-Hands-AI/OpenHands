import React from "react";

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-[#2c2f36] rounded ${className}`} />;
}
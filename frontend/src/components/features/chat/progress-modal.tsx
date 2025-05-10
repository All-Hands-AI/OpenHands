import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppSelector } from "#/hooks/redux/use-app-selector";
import { Dialog } from "#/components/shared/dialog";
import { Button } from "#/components/shared/buttons/button";
import { PayloadAction } from "@reduxjs/toolkit";
import { OpenHandsAction } from "#/types/core/actions";
import { cn } from "#/utils/utils";

interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentActionId?: number;
}

export function ProgressModal({ isOpen, onClose, currentActionId }: ProgressModalProps) {
  const { t } = useTranslation();
  const messages = useAppSelector((state) => state.chat.messages);
  const [actionData, setActionData] = useState<{
    actions: PayloadAction<OpenHandsAction>[];
    scores: number[];
  }>({ actions: [], scores: [] });
  const [hoveredAction, setHoveredAction] = useState<{
    action: PayloadAction<OpenHandsAction>;
    score: number;
    index: number;
  } | null>(null);
  
  const svgRef = useRef<SVGSVGElement>(null);

  // Extract all actions with critic scores
  useEffect(() => {
    if (isOpen) {
      const actionsWithScores = messages
        .filter((msg) => msg.action && msg.criticScore !== undefined)
        .map((msg) => ({
          action: msg.action as PayloadAction<OpenHandsAction>,
          score: msg.criticScore as number
        }));
      
      setActionData({
        actions: actionsWithScores.map(item => item.action),
        scores: actionsWithScores.map(item => item.score)
      });
    }
  }, [isOpen, messages]);

  // Function to get action type display name
  const getActionTypeName = (action: PayloadAction<OpenHandsAction>) => {
    const actionType = action.payload.type;
    return actionType.charAt(0).toUpperCase() + actionType.slice(1);
  };

  // Function to get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return "rgb(34, 197, 94)"; // green-500
    if (score >= 0.4) return "rgb(234, 179, 8)"; // yellow-500
    return "rgb(239, 68, 68)"; // red-500
  };

  // Function to format score as percentage
  const formatScore = (score: number) => {
    return `${Math.round(score * 100)}%`;
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={t("Agent Progress Visualization")}
      className="w-full max-w-3xl"
    >
      <div className="p-4">
        <div className="mb-4">
          <h3 className="text-lg font-medium">{t("Critic Score Timeline")}</h3>
          <p className="text-sm text-gray-500">
            {t("This visualization shows the critic score for each action in the conversation.")}
          </p>
        </div>
        
        {/* Visualization */}
        <div className="relative h-64 border border-gray-200 rounded-lg p-4 mb-4">
          {actionData.actions.length > 0 ? (
            <>
              <svg 
                ref={svgRef}
                className="w-full h-full" 
                viewBox={`0 0 ${actionData.actions.length * 50} 100`}
                preserveAspectRatio="none"
              >
                {/* Draw the line connecting all points */}
                <polyline
                  points={actionData.scores
                    .map((score, i) => `${i * 50 + 25},${100 - score * 100}`)
                    .join(" ")}
                  fill="none"
                  stroke="rgb(59, 130, 246)" // blue-500
                  strokeWidth="2"
                />
                
                {/* Draw dots for each action */}
                {actionData.scores.map((score, i) => (
                  <g key={i}>
                    <circle
                      cx={i * 50 + 25}
                      cy={100 - score * 100}
                      r={currentActionId === actionData.actions[i].payload.id ? 6 : 4}
                      fill={getScoreColor(score)}
                      stroke={currentActionId === actionData.actions[i].payload.id ? "black" : "white"}
                      strokeWidth="2"
                      className="cursor-pointer transition-all duration-200"
                      onMouseEnter={() => setHoveredAction({
                        action: actionData.actions[i],
                        score,
                        index: i
                      })}
                      onMouseLeave={() => setHoveredAction(null)}
                    />
                  </g>
                ))}
              </svg>
              
              {/* Tooltip */}
              {hoveredAction && (
                <div 
                  className="absolute bg-white shadow-lg rounded-md p-2 z-10 border border-gray-200 max-w-xs"
                  style={{
                    left: `${(hoveredAction.index / (actionData.actions.length - 1 || 1)) * 100}%`,
                    top: `${100 - hoveredAction.score * 100}%`,
                    transform: "translate(-50%, -120%)"
                  }}
                >
                  <div className="text-sm font-medium">
                    {getActionTypeName(hoveredAction.action)}
                  </div>
                  <div className="text-xs text-gray-500">
                    ID: {hoveredAction.action.payload.id}
                  </div>
                  <div className="text-xs">
                    Score: <span className={cn(
                      "font-medium",
                      hoveredAction.score >= 0.7 ? "text-green-500" : 
                      hoveredAction.score >= 0.4 ? "text-yellow-500" : "text-red-500"
                    )}>
                      {formatScore(hoveredAction.score)}
                    </span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              {t("No actions with critic scores available")}
            </div>
          )}
        </div>
        
        {/* Legend */}
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-xs">Good (≥70%)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-xs">Average (40-69%)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-xs">Poor (&lt;40%)</span>
          </div>
        </div>
        
        <div className="flex justify-end">
          <Button onClick={onClose} variant="secondary">
            {t("Close")}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  Button,
} from "@heroui/react";
import { PayloadAction } from "@reduxjs/toolkit";
import { OpenHandsAction } from "../../../types/core/actions";
import { cn } from "../../../utils/utils";
import { RootState } from "../../../store";

interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentActionId?: number;
}

export function ProgressModal({
  isOpen,
  onClose,
  currentActionId,
}: ProgressModalProps) {
  const { t } = useTranslation();
  const messages = useSelector((state: RootState) => state.chat.messages);
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
        .filter(
          (msg: {
            action?: PayloadAction<OpenHandsAction>;
            criticScore?: number;
          }) => msg.action && msg.criticScore !== undefined,
        )
        .map(
          (msg: {
            action: PayloadAction<OpenHandsAction>;
            criticScore: number;
          }) => ({
            action: msg.action as PayloadAction<OpenHandsAction>,
            score: msg.criticScore as number,
          }),
        );

      setActionData({
        actions: actionsWithScores.map(
          (item: { action: PayloadAction<OpenHandsAction>; score: number }) =>
            item.action,
        ),
        scores: actionsWithScores.map(
          (item: { action: PayloadAction<OpenHandsAction>; score: number }) =>
            item.score,
        ),
      });
    }
  }, [isOpen, messages]);

  // Function to get action type display name
  const getActionTypeName = (action: PayloadAction<OpenHandsAction>) => {
    const actionType = action.payload.action;
    return actionType.charAt(0).toUpperCase() + actionType.slice(1);
  };

  // Function to get color based on score using a continuous gradient
  const getScoreColor = (score: number) => {
    // Convert score to a hue value (0-120, where 0 is red and 120 is green)
    const hue = Math.round(score * 120);
    return `hsl(${hue}, 100%, 40%)`;
  };

  // Function to get text color class based on score
  const getScoreTextColorClass = (score: number) => {
    // We'll use a few discrete classes for text since we can't use arbitrary CSS in class names as easily
    if (score >= 0.8) return "text-green-500";
    if (score >= 0.6) return "text-lime-500";
    if (score >= 0.4) return "text-yellow-500";
    if (score >= 0.2) return "text-orange-500";
    return "text-red-500";
  };

  // Function to format score as percentage
  const formatScore = (score: number) => `${Math.round(score * 100)}%`;

  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={onClose}
      backdrop="blur"
      hideCloseButton
      size="lg"
      className="bg-base-secondary rounded-lg"
    >
      <ModalContent className="w-full max-w-3xl p-4">
        <ModalHeader className="flex flex-col p-0">
          <h2 className="text-xl font-semibold">
            {t("AGENT_PROGRESS_VISUALIZATION")}
          </h2>
        </ModalHeader>
        <ModalBody className="px-0 py-4">
          <div className="p-4">
            <div className="mb-4">
              <h3 className="text-lg font-medium">
                {t("CRITIC_SCORE_TIMELINE")}
              </h3>
              <p className="text-sm text-gray-500">
                {t("CRITIC_SCORE_VISUALIZATION_DESCRIPTION")}
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
                        .map(
                          (score, i) => `${i * 50 + 25},${100 - score * 100}`,
                        )
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
                          r={
                            currentActionId === actionData.actions[i].payload.id
                              ? 6
                              : 4
                          }
                          fill={getScoreColor(score)}
                          stroke={
                            currentActionId === actionData.actions[i].payload.id
                              ? "black"
                              : "white"
                          }
                          strokeWidth="2"
                          className="cursor-pointer transition-all duration-200"
                          onMouseEnter={() =>
                            setHoveredAction({
                              action: actionData.actions[i],
                              score,
                              index: i,
                            })
                          }
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
                        transform: `translate(-50%, -120%)`, // Position tooltip above the point
                      }}
                    >
                      <div className="text-sm font-medium">
                        {getActionTypeName(hoveredAction.action)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {t("ACTION_ID")}: {hoveredAction.action.payload.id}
                      </div>
                      <div className="text-xs">
                        {t("CRITIC_SCORE")}:{" "}
                        <span
                          className={cn(
                            "font-medium",
                            getScoreTextColorClass(hoveredAction.score),
                          )}
                        >
                          {formatScore(hoveredAction.score)}
                        </span>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  {t("NO_CRITIC_SCORES_AVAILABLE")}
                </div>
              )}
            </div>

            {/* Gradient Legend */}
            <div className="mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs">{t("CRITIC_SCORE_SCALE")}:</span>
                <div className="flex-1 h-4 rounded-md" style={{
                  background: "linear-gradient(to right, hsl(0, 100%, 40%), hsl(60, 100%, 40%), hsl(120, 100%, 40%))"
                }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-xs text-red-500">0%</span>
                <span className="text-xs text-yellow-500">50%</span>
                <span className="text-xs text-green-500">100%</span>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={onClose} variant="flat">
                {t("Close")}
              </Button>
            </div>
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}

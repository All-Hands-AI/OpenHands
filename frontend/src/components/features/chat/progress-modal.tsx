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
import { Message } from "../../../message";

interface ProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentActionId?: number;
}

interface TooltipProps {
  position: { x: number; y: number };
  containerRef: React.RefObject<HTMLDivElement | null>;
  children: React.ReactNode;
}

function Tooltip({ position, containerRef, children }: TooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!tooltipRef.current || !containerRef.current) return;

    const tooltip = tooltipRef.current;
    const container = containerRef.current;
    const tooltipWidth = tooltip.offsetWidth;
    const tooltipHeight = tooltip.offsetHeight;
    const containerWidth = container.offsetWidth;
    const containerHeight = container.offsetHeight;

    // Calculate initial position
    let x = position.x - tooltipWidth / 2;
    let y = position.y - tooltipHeight - 12;

    // Adjust for container boundaries
    x = Math.max(8, Math.min(x, containerWidth - tooltipWidth - 8));
    y = Math.max(8, Math.min(y, containerHeight - tooltipHeight - 8));

    setTooltipPosition({ x, y });
  }, [position, containerRef]);

  return (
    <div
      ref={tooltipRef}
      className="absolute z-10 border border-gray-200 max-w-xs bg-white shadow-lg rounded-md p-3"
      style={{
        left: tooltipPosition.x,
        top: tooltipPosition.y,
        pointerEvents: "none",
      }}
    >
      {children}
    </div>
  );
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
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Extract all actions with critic scores
  useEffect(() => {
    if (isOpen) {
      const actionsWithScores = messages
        .filter(
          (msg: Message) =>
            msg.action !== undefined && msg.criticScore !== undefined,
        )
        .map((msg: Message) => ({
          action: msg.action as PayloadAction<OpenHandsAction>,
          score: msg.criticScore as number,
        }));

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

  // Function to get color based on score using 10 discrete bins
  const getScoreColor = (score: number) => {
    // Use 10 discrete bins from red (0) to green (1)
    if (score < 0.1) return "rgb(220, 38, 38)"; // red-600
    if (score < 0.2) return "rgb(239, 68, 68)"; // red-500
    if (score < 0.3) return "rgb(234, 88, 12)"; // orange-600
    if (score < 0.4) return "rgb(249, 115, 22)"; // orange-500
    if (score < 0.5) return "rgb(202, 138, 4)"; // yellow-600
    if (score < 0.6) return "rgb(234, 179, 8)"; // yellow-500
    if (score < 0.7) return "rgb(101, 163, 13)"; // lime-600
    if (score < 0.8) return "rgb(132, 204, 22)"; // lime-500
    if (score < 0.9) return "rgb(22, 163, 74)"; // green-600
    return "rgb(34, 197, 94)"; // green-500
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

  // SVG padding
  const SVG_WIDTH = Math.max(actionData.actions.length * 50, 400);
  const SVG_HEIGHT = 256;
  const PADDING_X = 32;
  const PADDING_Y = 24;
  const plotWidth = SVG_WIDTH - 2 * PADDING_X;
  const plotHeight = SVG_HEIGHT - 2 * PADDING_Y;
  const n = actionData.actions.length;

  // Helper to get X/Y positions scaled to fill SVG
  const getX = (i: number) => {
    if (n === 1) return SVG_WIDTH / 2;
    return PADDING_X + (plotWidth * i) / (n - 1);
  };
  const getY = (score: number) => PADDING_Y + plotHeight * (1 - score);

  // Tooltip rendering logic extracted to a variable to avoid IIFE in JSX
  let tooltip = null;
  if (hoveredAction) {
    const cx = getX(hoveredAction.index);
    const cy = getY(hoveredAction.score);
    let left = cx;
    if (scrollContainerRef.current) {
      left = cx - scrollContainerRef.current.scrollLeft;
    }
    // Make tooltip closer to the point (smaller vertical offset)
    tooltip = (
      <Tooltip
        position={{ x: left, y: cy - 8 }} // 8px above the point
        containerRef={scrollContainerRef}
      >
        <div className="text-base font-semibold text-gray-900 mb-1">
          {getActionTypeName(hoveredAction.action)}
        </div>
        <div className="text-xs text-gray-500 mb-1">
          {t("ACTION_ID")}:{" "}
          <span className="text-gray-700">
            {hoveredAction.action.payload.id}
          </span>
        </div>
        <div className="text-xs text-gray-700">
          {t("CRITIC_SCORE")}:{" "}
          <span
            className={cn(
              "font-bold",
              getScoreTextColorClass(hoveredAction.score),
            )}
          >
            {formatScore(hoveredAction.score)}
          </span>
        </div>
      </Tooltip>
    );
  }

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
            <div
              className="relative h-64 border border-gray-200 rounded-lg p-4 mb-4 overflow-x-auto"
              ref={scrollContainerRef}
            >
              {actionData.actions.length > 0 ? (
                <>
                  <div style={{ minWidth: `${SVG_WIDTH}px` }}>
                    <svg
                      ref={svgRef}
                      width={SVG_WIDTH}
                      height={SVG_HEIGHT}
                      viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
                      preserveAspectRatio={t("SVG_PRESERVE_ASPECT_RATIO")}
                      style={{ display: "block", margin: "0 auto" }}
                    >
                      {/* Draw the line connecting all points */}
                      <polyline
                        points={actionData.scores
                          .map((score, i) => `${getX(i)},${getY(score)}`)
                          .join(" ")}
                        fill="none"
                        stroke="rgb(59, 130, 246)" // blue-500
                        strokeWidth="2"
                      />

                      {/* Draw dots for each action */}
                      {actionData.scores.map((score, i) => (
                        <g key={i}>
                          <circle
                            cx={getX(i)}
                            cy={getY(score)}
                            r={
                              currentActionId ===
                              actionData.actions[i].payload.id
                                ? 6
                                : 4
                            }
                            fill={getScoreColor(score)}
                            stroke={
                              currentActionId ===
                              actionData.actions[i].payload.id
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
                  </div>
                  {tooltip}
                </>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  {t("NO_CRITIC_SCORES_AVAILABLE")}
                </div>
              )}
            </div>

            {/* Discrete Bins Legend */}
            <div className="mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs">{t("CRITIC_SCORE_SCALE")}:</span>
                <div className="flex-1 h-4 rounded-md flex">
                  <div className="flex-1 h-full bg-red-600" />
                  <div className="flex-1 h-full bg-red-500" />
                  <div className="flex-1 h-full bg-orange-600" />
                  <div className="flex-1 h-full bg-orange-500" />
                  <div className="flex-1 h-full bg-yellow-600" />
                  <div className="flex-1 h-full bg-yellow-500" />
                  <div className="flex-1 h-full bg-lime-600" />
                  <div className="flex-1 h-full bg-lime-500" />
                  <div className="flex-1 h-full bg-green-600" />
                  <div className="flex-1 h-full bg-green-500" />
                </div>
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

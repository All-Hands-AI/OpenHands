import React, { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { ExtraProps } from "react-markdown";
import { Typography } from "#/ui/typography";
import { MarkdownRenderer } from "#/components/features/markdown/markdown-renderer";
import { planComponents } from "#/components/features/markdown/plan-components";
import { DEEP_PLAN_PHASES, type DeepPlanPhaseId } from "#/utils/deep-plan";
import {
  DEEP_PLAN_CITATION_SCHEME,
  deepPlanDocumentId,
  deepPlanSectionId,
  definedSectionOfHeading,
  linkifyCitations,
  parseDeepPlanCitation,
} from "#/utils/deep-plan-reference";
import { DEEP_PLAN_PHASE_LABEL_KEY } from "#/utils/deep-plan-messages";

function textOf(node: React.ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  if (React.isValidElement(node)) {
    return textOf((node.props as { children?: React.ReactNode }).children);
  }
  return "";
}

interface DeepPlanDocumentProps {
  phase: DeepPlanPhaseId;
  phaseLabel: string;
  content: string;
  open: boolean;
}

/**
 * Renders one phase document as a section of the chain with reference
 * navigation. Each real citation becomes a link to the cited section, and
 * clicking it scrolls that section into view. A numbered heading gets an anchor
 * span so a citation link has a stable target.
 *
 * Memoized: the chain re-renders on every parent render (e.g. a websocket
 * status tick), but a phase's Markdown body only changes when the document
 * itself does.
 */
export const DeepPlanDocument = React.memo(function DeepPlanDocument({
  phase,
  phaseLabel,
  content,
  open,
}: DeepPlanDocumentProps) {
  const handleCitationClick = useCallback(
    (event: React.MouseEvent<HTMLAnchorElement>, href: string | undefined) => {
      const target = parseDeepPlanCitation(href);
      if (!target) return;
      event.preventDefault();
      const ownerDocument = event.currentTarget.ownerDocument;
      const element =
        ownerDocument.getElementById(
          deepPlanSectionId(target.phase, target.section),
        ) ?? ownerDocument.getElementById(deepPlanDocumentId(target.phase));
      element?.scrollIntoView({ behavior: "smooth", block: "start" });
    },
    [],
  );

  const citationAnchor = useCallback(
    ({
      href,
      children,
      ...rest
    }: React.ClassAttributes<HTMLAnchorElement> &
      React.AnchorHTMLAttributes<HTMLAnchorElement> &
      ExtraProps) => {
      if (!href?.startsWith(DEEP_PLAN_CITATION_SCHEME)) {
        // A non-citation link is an ordinary external link; render it through
        // the plan anchor so it keeps `target="_blank"` and
        // `rel="noopener noreferrer"` instead of a bare `<a>`.
        const PlanAnchor = planComponents.a;
        return (
          <PlanAnchor href={href} {...rest}>
            {children}
          </PlanAnchor>
        );
      }
      return (
        <a
          href={href}
          data-testid="deep-plan-citation"
          className="text-blue-500 hover:underline"
          onClick={(event) => handleCitationClick(event, href)}
        >
          {children}
        </a>
      );
    },
    [handleCitationClick],
  );

  const components = useMemo(() => {
    const withSectionAnchor = (Heading: typeof planComponents.h2) =>
      function SectionAnchoredHeading({
        children,
        ...rest
      }: React.ComponentProps<typeof Heading>) {
        const section = definedSectionOfHeading(textOf(children)) ?? undefined;
        return (
          <Heading {...rest}>
            {section ? (
              <span id={deepPlanSectionId(phase, section)}>{children}</span>
            ) : (
              children
            )}
          </Heading>
        );
      };
    return {
      ...planComponents,
      h1: withSectionAnchor(planComponents.h1),
      h2: withSectionAnchor(planComponents.h2),
      h3: withSectionAnchor(planComponents.h3),
      h4: withSectionAnchor(planComponents.h4),
      h5: withSectionAnchor(planComponents.h5),
      h6: withSectionAnchor(planComponents.h6),
      a: citationAnchor,
    };
  }, [phase, citationAnchor]);

  return (
    <li
      id={deepPlanDocumentId(phase)}
      data-testid={`deep-plan-document-${phase}`}
      data-open={open ? "true" : "false"}
      className="flex flex-col gap-1"
    >
      <Typography.Text className="text-xs font-medium">
        {phaseLabel}
      </Typography.Text>
      <MarkdownRenderer
        includeStandard
        includeHeadings
        extraHrefProtocols={[DEEP_PLAN_CITATION_SCHEME.replace(/:$/, "")]}
        components={components}
      >
        {linkifyCitations(content, phase)}
      </MarkdownRenderer>
    </li>
  );
});

/**
 * Renders the whole produced document chain, each document as a section with
 * reference navigation. A citation the validator rejects is left as plain text
 * rather than a dead link, so the chain only offers links the checkpoint
 * agrees are valid.
 */
export function DeepPlanDocumentChain({
  documents,
  expandedPhase,
}: {
  documents: Partial<Record<DeepPlanPhaseId, string>>;
  expandedPhase: DeepPlanPhaseId;
}) {
  const { t } = useTranslation("openhands");

  const orderedDocuments = useMemo(
    () =>
      DEEP_PLAN_PHASES.flatMap((phase) => {
        const content = documents[phase.id];
        return content === undefined
          ? []
          : [
              {
                phase: phase.id,
                label:
                  phase.outputFile ?? t(DEEP_PLAN_PHASE_LABEL_KEY[phase.id]),
                content,
              },
            ];
      }),
    [documents, t],
  );

  return (
    <ol className="flex flex-col gap-4" data-testid="deep-plan-document-chain">
      {orderedDocuments.map((doc) => (
        <DeepPlanDocument
          key={doc.phase}
          phase={doc.phase}
          phaseLabel={doc.label}
          content={doc.content}
          open={doc.phase === expandedPhase}
        />
      ))}
    </ol>
  );
}

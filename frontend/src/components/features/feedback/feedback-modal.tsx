import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";

interface FeedbackModalProps {
  onClose: () => void;
  isOpen: boolean;
  polarity: "positive" | "negative";
  onSubmit: (categories: string[], additionalFeedback: string) => void;
}

// Define feedback categories - using function to access translations
const getPositiveCategories = (t: (key: string) => string) => [
  t(I18nKey.FEEDBACK$CATEGORY_SOLVED_COMPLETELY),
  t(I18nKey.FEEDBACK$CATEGORY_GOOD_CODE),
  t(I18nKey.FEEDBACK$CATEGORY_CLEAR_EXPLANATIONS),
  t(I18nKey.FEEDBACK$CATEGORY_EFFICIENT_SOLUTION),
  t(I18nKey.FEEDBACK$CATEGORY_GOOD_CONTEXT),
];

const getNegativeCategories = (t: (key: string) => string) => [
  t(I18nKey.FEEDBACK$CATEGORY_STUCK_LOOP),
  t(I18nKey.FEEDBACK$CATEGORY_POOR_CONTEXT),
  t(I18nKey.FEEDBACK$CATEGORY_WRONG_EDITS),
  t(I18nKey.FEEDBACK$CATEGORY_INCOMPLETE),
  t(I18nKey.FEEDBACK$CATEGORY_POOR_CODE),
  t(I18nKey.FEEDBACK$CATEGORY_SLOW),
];

export function FeedbackModal({
  onClose,
  isOpen,
  polarity,
  onSubmit,
}: FeedbackModalProps) {
  const { t } = useTranslation();
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>(
    [],
  );
  const [additionalFeedback, setAdditionalFeedback] = React.useState("");

  // Reset state when modal opens
  React.useEffect(() => {
    if (isOpen) {
      setSelectedCategories([]);
      setAdditionalFeedback("");
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const categories =
    polarity === "positive"
      ? getPositiveCategories(t)
      : getNegativeCategories(t);

  const handleCategoryToggle = (category: string) => {
    setSelectedCategories((prev) => {
      if (prev.includes(category)) {
        return prev.filter((c) => c !== category);
      }
      return [...prev, category];
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(selectedCategories, additionalFeedback);
    onClose();
  };

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody className="border border-tertiary max-w-md">
        <BaseModalTitle
          title={
            polarity === "positive"
              ? t(I18nKey.FEEDBACK$POSITIVE_TITLE)
              : t(I18nKey.FEEDBACK$NEGATIVE_TITLE)
          }
        />
        <BaseModalDescription
          description={t(I18nKey.FEEDBACK$ENHANCED_DESCRIPTION)}
        />

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium">
              {t(I18nKey.FEEDBACK$CATEGORIES_LABEL)}
            </span>
            <div className="grid grid-cols-1 gap-2">
              {categories.map((category) => (
                <label
                  key={category}
                  className="flex items-center gap-2 cursor-pointer p-2 rounded hover:bg-gray-800"
                >
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => handleCategoryToggle(category)}
                    className="h-4 w-4"
                  />
                  <span className="text-sm">{category}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium">
              {t(I18nKey.FEEDBACK$ADDITIONAL_FEEDBACK_LABEL)}
            </span>
            <textarea
              value={additionalFeedback}
              onChange={(e) => setAdditionalFeedback(e.target.value)}
              placeholder={t(I18nKey.FEEDBACK$ADDITIONAL_FEEDBACK_PLACEHOLDER)}
              className="bg-[#27272A] px-3 py-2 rounded min-h-[100px] text-sm"
            />
          </div>

          <div className="flex gap-2 mt-2">
            <BrandButton type="submit" variant="primary" className="grow">
              {t(I18nKey.FEEDBACK$SUBMIT_LABEL)}
            </BrandButton>
            <BrandButton
              type="button"
              variant="secondary"
              className="grow"
              onClick={onClose}
            >
              {t(I18nKey.FEEDBACK$CANCEL_LABEL)}
            </BrandButton>
          </div>
        </form>
      </ModalBody>
    </ModalBackdrop>
  );
}

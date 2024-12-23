import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '#/store';
import { InstructionsPanel } from '@/components/features/instructions/instructions-panel';

export default function InstructionsRoute() {
  const { selectedRepository } = useSelector((state: RootState) => state.initalQuery);

  // TODO: Implement logic to fetch hasInstructions and tutorialUrl
  const hasInstructions = false;
  const tutorialUrl = '';

  const handleAddInstructions = () => {
    // TODO: Implement logic to add instructions
    console.log('Add instructions clicked');
  };

  return (
    <InstructionsPanel
      repoName={selectedRepository}
      hasInstructions={hasInstructions}
      tutorialUrl={tutorialUrl}
      onAddInstructions={handleAddInstructions}
    />
  );
}
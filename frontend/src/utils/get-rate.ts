import React from "react";

interface UseRateProps {
  threshold: number;
}

const DEFAULT_CONFIG: UseRateProps = { threshold: 1000 };

export const useRate = (config = DEFAULT_CONFIG) => {
  const [items, setItems] = React.useState<number[]>([]);
  const [rate, setRate] = React.useState<number | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<number | null>(null);
  const [isUnderThreshold, setIsUnderThreshold] = React.useState(true);

  const record = (entry: number) => {
    setItems((prev) => [...prev, entry]);
    setLastUpdated(new Date().getTime());
  };

  const updateRate = () => {
    if (items.length > 1) {
      const newRate = items[items.length - 1] - items[items.length - 2];
      setRate(newRate);

      if (newRate <= config.threshold) setIsUnderThreshold(true);
      else setIsUnderThreshold(false);
    }
  };

  React.useEffect(() => {
    updateRate();
  }, [items]);

  React.useEffect(() => {
    const intervalId = setInterval(() => {
      if (lastUpdated !== null) {
        const timeSinceLastUpdate = new Date().getTime() - lastUpdated;
        setIsUnderThreshold(timeSinceLastUpdate <= config.threshold);
      } else {
        setIsUnderThreshold(false);
      }
    }, config.threshold);

    return () => clearInterval(intervalId);
  }, [lastUpdated, config.threshold]);

  return {
    items,
    rate,
    lastUpdated,
    isUnderThreshold,
    record,
  };
};

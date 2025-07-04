import { useCallback, useState } from "react";

type ArrayActions<T> = {
  push: (value: T | T[]) => void;
  replace: (value: T | T[]) => void;
  addAtIndex: (index: number, value: T) => void;
  removeAt: (index: number) => void;
  remove: (value: T, compareBy?: keyof T) => void;
  subset: (indexStart: number, indexEnd: number) => void;
  clear: () => void;
};

export function useArray<T>(initialValue: T | T[]): [T[], ArrayActions<T>] {
  const [array, setArray] = useState<T[]>(
    Array.isArray(initialValue) ? initialValue : [initialValue]
  );

  const push = useCallback((value: T | T[]) => {
    const values = Array.isArray(value) ? value : [value];
    setArray((prev) => [...prev, ...values]);
  }, []);

  const replace = useCallback((value: T | T[]) => {
    setArray(Array.isArray(value) ? value : [value]);
  }, []);

  const addAtIndex = useCallback((index: number, value: T) => {
    setArray((prev) => [
      ...prev.slice(0, index + 1),
      value,
      ...prev.slice(index + 1),
    ]);
  }, []);

  const removeAt = useCallback((index: number) => {
    setArray((prev) => [...prev.slice(0, index), ...prev.slice(index + 1)]);
  }, []);

  const remove = useCallback((value: T, compareBy?: keyof T) => {
    setArray((prev) => {
      const index = prev.findIndex((item) =>
        compareBy
          ? isEqual(item[compareBy], value[compareBy])
          : isEqual(item, value)
      );
      return index >= 0
        ? [...prev.slice(0, index), ...prev.slice(index + 1)]
        : prev;
    });
  }, []);

  const subset = useCallback((indexStart: number, indexEnd: number) => {
    setArray((prev) => prev.slice(indexStart, indexEnd + 1));
  }, []);

  const clear = useCallback(() => {
    setArray([]);
  }, []);

  return [
    array,
    { push, replace, addAtIndex, removeAt, remove, subset, clear },
  ];
}

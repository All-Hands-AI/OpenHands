export function invariant(condition: boolean, message: string) {
  if (process.env.NODE_ENV !== "development") {
    return;
  }
  if (!condition) {
    const error = new Error(message);
    error.name = "Invariant Violation";
    throw error;
  }
}

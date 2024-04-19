import { removeEmptyNodes } from "./utils";

test("removeEmptyNodes removes empty arrays", () => {
  const root = {
    name: "a",
    children: [
      {
        name: "b",
        children: [],
      },
      {
        name: "c",
        children: [
          {
            name: "d",
            children: [],
          },
        ],
      },
    ],
  };

  expect(removeEmptyNodes(root)).toEqual({
    name: "a",
    children: [
      {
        name: "b",
      },
      {
        name: "c",
        children: [
          {
            name: "d",
          },
        ],
      },
    ],
  });
});

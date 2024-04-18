import { removeEmptyNodes } from "./utils";

test("removeEmptyNodes removes empty arrays", () => {
  const tree = [
    {
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
    },
  ];

  expect(removeEmptyNodes(tree)).toEqual([
    {
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
    },
  ]);
});

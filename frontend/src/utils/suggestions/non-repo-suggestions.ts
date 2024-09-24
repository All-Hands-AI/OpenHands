const KEY_1 = "Build an app to view pull requests";
const VALUE_1 = `I want to create a React app to view all of the open pull 
requests that exist on all of my team's github repos. Here 
are some details:

1. Please initialize the app using vite and react-ts.
2. You can test the app on the https://github.com/OpenDevin/
   github org
3. I have provided a github token in the environment (the
   variable name is $GITHUB_TOKEN)
4. It should have a dropdown that allows me to select a
   single repo within the org.
5. There should be tests written using vitest.

When things are working, initialize a github repo, create
a .gitignore file, and commit the changes.`;

const KEY_2 = "Build a todo list application";
const VALUE_2 = `I want to create a VueJS app that allows me to:
* See all the items on my todo list
* add a new item to the list
* mark an item as done
* totally remove an item from the list
* change the text of an item
* set a due date on the item

This should be a client-only app with no backend. The list should persist in localStorage.

Please add tests for all of the above and make sure they pass`;

const KEY_3 = "Write a bash script that shows the top story on Hacker News";
const VALUE_3 = `Please write a bash script which displays the top story on Hacker News. It should show the title, the link, and the number of points.

The script should only use tools that are widely available on unix systems, like curl and grep.`;

export const NON_REPO_SUGGESTIONS: Record<string, string> = {
  [KEY_1]: VALUE_1,
  [KEY_2]: VALUE_2,
  [KEY_3]: VALUE_3,
};

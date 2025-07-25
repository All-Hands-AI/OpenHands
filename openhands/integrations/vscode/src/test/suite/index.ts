import * as path from "path";
import Mocha = require("mocha"); // Changed import style
import { glob } from "glob"; // Use named import for modern glob

export function run(): Promise<void> {
  // Create the mocha test
  const mocha = new Mocha({
    // This should now work with the changed import
    ui: "tdd", // Use TDD interface
    color: true, // Colored output
    timeout: 15000, // Increased timeout for extension tests
  });

  const testsRoot = path.resolve(__dirname, ".."); // Root of the /src/test folder (compiled to /out/test)

  return new Promise((c, e) => {
    (async () => {
      try {
        // Use glob to find all test files (ending with .test.js in the compiled output)
        const files = await glob("**/**.test.js", { cwd: testsRoot });

        // Add files to the test suite
        files.forEach((f: string) => mocha.addFile(path.resolve(testsRoot, f)));

        try {
          // Run the mocha test
          mocha.run((failures: number) => {
            if (failures > 0) {
              e(new Error(`${failures} tests failed.`));
            } else {
              c();
            }
          });
        } catch (err) {
          console.error(err);
          e(err);
        }
      } catch (err) {
        console.error("Error finding test files:", err);
        e(err);
      }
    })();
  });
}

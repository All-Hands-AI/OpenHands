import * as path from "path";
import Mocha = require("mocha");
import { glob } from "glob"; // Updated for glob v9+ API

export async function run(): Promise<void> {
  // Create the mocha test
  const mocha = new Mocha({
    // This should now work with the changed import
    ui: "tdd", // Use TDD interface
    color: true, // Colored output
    timeout: 15000, // Increased timeout for extension tests
  });

  const testsRoot = path.resolve(__dirname, ".."); // Root of the /src/test folder (compiled to /out/test)

  try {
    // Use glob to find all test files (ending with .test.js in the compiled output)
    const files = await glob("**/**.test.js", { cwd: testsRoot });

    // Add files to the test suite
    files.forEach((f: string) => mocha.addFile(path.resolve(testsRoot, f)));

    // Run the mocha test
    return await new Promise<void>((resolve, reject) => {
      mocha.run((failures: number) => {
        if (failures > 0) {
          reject(new Error(`${failures} tests failed.`));
        } else {
          resolve();
        }
      });
    });
  } catch (err) {
    console.error(err);
    throw err;
  }
}

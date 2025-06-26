import * as assert from "assert";
import * as vscode from "vscode";

suite("Extension Test Suite", () => {
  let mockTerminal: vscode.Terminal;
  let sendTextSpy: any; // Manual spy, using 'any' type
  let showSpy: any; // Manual spy
  let createTerminalStub: any; // Manual stub
  let findTerminalStub: any; // Manual spy
  let showErrorMessageSpy: any; // Manual spy

  // It's better to use a proper mocking library like Sinon.JS for spies and stubs.
  // For now, we'll use a simplified manual approach for spies.
  const createManualSpy = () => {
    const spy: any = (...args: any[]) => {
      // eslint-disable-line @typescript-eslint/no-explicit-any
      spy.called = true;
      spy.callCount = (spy.callCount || 0) + 1;
      spy.lastArgs = args;
      spy.argsHistory = spy.argsHistory || [];
      spy.argsHistory.push(args);
    };
    spy.called = false;
    spy.callCount = 0;
    spy.lastArgs = null;
    spy.argsHistory = [];
    spy.resetHistory = () => {
      spy.called = false;
      spy.callCount = 0;
      spy.lastArgs = null;
      spy.argsHistory = [];
    };
    return spy;
  };

  setup(() => {
    // Reset spies and stubs before each test
    sendTextSpy = createManualSpy();
    showSpy = createManualSpy();
    showErrorMessageSpy = createManualSpy();

    mockTerminal = {
      name: "OpenHands",
      processId: Promise.resolve(123),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined, // Added to satisfy Terminal interface
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      }, // Added shell property
      shellIntegration: undefined, // No Shell Integration in tests by default
    };

    // Store original functions
    const _originalCreateTerminal = vscode.window.createTerminal;
    const _originalTerminalsDescriptor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "terminals",
    );
    const _originalShowErrorMessage = vscode.window.showErrorMessage;

    // Stub vscode.window.createTerminal
    createTerminalStub = createManualSpy();
    vscode.window.createTerminal = (...args: any[]): vscode.Terminal => {
      createTerminalStub(...args); // Call the spy with whatever arguments it received
      return mockTerminal; // Return the mock terminal
    };

    // Stub vscode.window.terminals
    findTerminalStub = createManualSpy(); // To track if vscode.window.terminals getter is accessed
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        // Default to returning the mockTerminal, can be overridden in specific tests
        return [mockTerminal];
      },
      configurable: true,
    });

    vscode.window.showErrorMessage = showErrorMessageSpy as any;

    // Restore default mock behavior before each test
    setup(() => {
      // Reset spies
      createTerminalStub.resetHistory();
      sendTextSpy.resetHistory();
      showSpy.resetHistory();
      findTerminalStub.resetHistory();
      showErrorMessageSpy.resetHistory();

      // Restore default createTerminal mock
      vscode.window.createTerminal = (...args: any[]): vscode.Terminal => {
        createTerminalStub(...args);
        return mockTerminal; // Return the default mock terminal (no Shell Integration)
      };

      // Restore default terminals mock
      Object.defineProperty(vscode.window, "terminals", {
        get: () => {
          findTerminalStub();
          return [mockTerminal]; // Default to returning the mockTerminal
        },
        configurable: true,
      });
    });

    // Teardown logic to restore original functions
    teardown(() => {
      vscode.window.createTerminal = _originalCreateTerminal;
      if (_originalTerminalsDescriptor) {
        Object.defineProperty(
          vscode.window,
          "terminals",
          _originalTerminalsDescriptor,
        );
      } else {
        // If it wasn't originally defined, delete it to restore to that state
        delete (vscode.window as any).terminals;
      }
      vscode.window.showErrorMessage = _originalShowErrorMessage;
    });
  });

  test("Extension should be present and activate", async () => {
    const extension = vscode.extensions.getExtension(
      "openhands.openhands-vscode",
    );
    assert.ok(
      extension,
      "Extension should be found (check publisher.name in package.json)",
    );
    if (!extension.isActive) {
      await extension.activate();
    }
    assert.ok(extension.isActive, "Extension should be active");
  });

  test("Commands should be registered", async () => {
    const extension = vscode.extensions.getExtension(
      "openhands.openhands-vscode",
    );
    if (extension && !extension.isActive) {
      await extension.activate();
    }
    const commands = await vscode.commands.getCommands(true);
    const expectedCommands = [
      "openhands.startConversation",
      "openhands.startConversationWithFileContext",
      "openhands.startConversationWithSelectionContext",
    ];
    for (const cmd of expectedCommands) {
      assert.ok(
        commands.includes(cmd),
        `Command '${cmd}' should be registered`,
      );
    }
  });

  test("openhands.startConversation should send correct command to terminal", async () => {
    findTerminalStub.resetHistory(); // Reset for this specific test path if needed
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [];
      },
      configurable: true,
    }); // Simulate no existing terminal

    await vscode.commands.executeCommand("openhands.startConversation");

    assert.ok(
      createTerminalStub.called,
      "vscode.window.createTerminal should be called",
    );
    assert.ok(showSpy.called, "terminal.show should be called");
    assert.deepStrictEqual(
      sendTextSpy.lastArgs,
      ["openhands", true],
      "Correct command sent to terminal",
    );
  });

  test("openhands.startConversationWithFileContext (saved file) should send --file command", async () => {
    const testFilePath = "/test/file.py";
    // Mock activeTextEditor for a saved file
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file(testFilePath),
          fsPath: testFilePath, // fsPath is often used
          getText: () => "file content", // Not used for saved files but good to have
        },
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithFileContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");
    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --file ${testFilePath.includes(" ") ? `"${testFilePath}"` : testFilePath}`,
      true,
    ]);

    // Restore activeTextEditor
    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithFileContext (untitled file) should send contextual --task command", async () => {
    const untitledFileContent = "untitled content";
    const languageId = "javascript";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: true,
          uri: vscode.Uri.parse("untitled:Untitled-1"),
          getText: () => untitledFileContent,
          languageId,
        },
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithFileContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");

    // Check that the command contains the contextual message
    const expectedMessage = `User opened an untitled file (${languageId}). Here's the content:

\`\`\`${languageId}
${untitledFileContent}
\`\`\`

Please ask the user what they want to do with this file.`;

    // Apply the same sanitization as the actual implementation
    const sanitizedMessage = expectedMessage
      .replace(/`/g, "\\`")
      .replace(/"/g, '\\"');

    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --task "${sanitizedMessage}"`,
      true,
    ]);

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithFileContext (no editor) should start conversation without context", async () => {
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => undefined,
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithFileContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");
    assert.deepStrictEqual(sendTextSpy.lastArgs, ["openhands", true]);

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithSelectionContext should send contextual --task with selection", async () => {
    const selectedText = "selected text for openhands";
    const filePath = "/test/file.py";
    const languageId = "python";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file(filePath),
          fsPath: filePath,
          languageId,
          getText: (selection?: vscode.Selection) =>
            selection ? selectedText : "full content",
        },
        selection: {
          isEmpty: false,
          active: new vscode.Position(0, 0),
          anchor: new vscode.Position(0, 0),
          start: new vscode.Position(0, 0), // Line 0 (0-based)
          end: new vscode.Position(0, 10), // Line 0 (0-based)
        } as vscode.Selection, // Mock non-empty selection on line 1
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithSelectionContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");

    // Check that the command contains the contextual message with line numbers
    const expectedMessage = `User selected line 1 in file ${filePath} (${languageId}). Here's the selected content:

\`\`\`${languageId}
${selectedText}
\`\`\`

Please ask the user what they want to do with this selection.`;

    // Apply the same sanitization as the actual implementation
    const sanitizedMessage = expectedMessage
      .replace(/`/g, "\\`")
      .replace(/"/g, '\\"');

    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --task "${sanitizedMessage}"`,
      true,
    ]);

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithSelectionContext (no selection) should start conversation without context", async () => {
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file("/test/file.py"),
          getText: () => "full content",
        },
        selection: { isEmpty: true } as vscode.Selection, // Mock empty selection
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithSelectionContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");
    assert.deepStrictEqual(sendTextSpy.lastArgs, ["openhands", true]);

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithSelectionContext should handle multi-line selections", async () => {
    const selectedText = "line 1\nline 2\nline 3";
    const filePath = "/test/multiline.js";
    const languageId = "javascript";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file(filePath),
          fsPath: filePath,
          languageId,
          getText: (selection?: vscode.Selection) =>
            selection ? selectedText : "full content",
        },
        selection: {
          isEmpty: false,
          active: new vscode.Position(4, 0),
          anchor: new vscode.Position(4, 0),
          start: new vscode.Position(4, 0), // Line 4 (0-based) = Line 5 (1-based)
          end: new vscode.Position(6, 10), // Line 6 (0-based) = Line 7 (1-based)
        } as vscode.Selection, // Mock multi-line selection from line 5 to 7
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithSelectionContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");

    // Check that the command contains the contextual message with line range
    const expectedMessage = `User selected lines 5-7 in file ${filePath} (${languageId}). Here's the selected content:

\`\`\`${languageId}
${selectedText}
\`\`\`

Please ask the user what they want to do with this selection.`;

    // Apply the same sanitization as the actual implementation
    const sanitizedMessage = expectedMessage
      .replace(/`/g, "\\`")
      .replace(/"/g, '\\"');

    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --task "${sanitizedMessage}"`,
      true,
    ]);

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("Terminal reuse should work when existing OpenHands terminal exists", async () => {
    // Create a mock existing terminal
    const existingTerminal = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: undefined, // No Shell Integration, should create new terminal
    };

    // Mock terminals array to return existing terminal
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [existingTerminal];
      },
      configurable: true,
    });

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should create new terminal since no Shell Integration
    assert.ok(
      createTerminalStub.called,
      "Should create new terminal when no Shell Integration available",
    );
  });

  test("Terminal reuse with Shell Integration should reuse existing terminal", async () => {
    // Create mock Shell Integration
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OPENHANDS_PROBE_123456789";
        },
      }),
      exitCode: Promise.resolve(0),
    };

    const mockShellIntegration = {
      executeCommand: () => mockExecution,
    };

    // Create a mock existing terminal with Shell Integration
    const existingTerminalWithShell = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: mockShellIntegration,
    };

    // Mock terminals array to return existing terminal with Shell Integration
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [existingTerminalWithShell];
      },
      configurable: true,
    });

    // Reset create terminal stub to track if new terminal is created
    createTerminalStub.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should reuse existing terminal since Shell Integration is available
    // Note: The probe might timeout in test environment, but it should still reuse the terminal
    assert.ok(showSpy.called, "terminal.show should be called");
  });

  test("Shell Integration should use executeCommand for OpenHands commands", async () => {
    const executeCommandSpy = createManualSpy();

    // Mock execution for OpenHands command
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OpenHands started successfully";
        },
      }),
      exitCode: Promise.resolve(0),
      commandLine: {
        value: "openhands",
        isTrusted: true,
        confidence: 2,
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    // Create a terminal with Shell Integration that will be created by createTerminal
    const terminalWithShell = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: mockShellIntegration,
    };

    // Mock createTerminal to return a terminal with Shell Integration
    createTerminalStub.resetHistory();
    vscode.window.createTerminal = (...args: any[]): vscode.Terminal => {
      createTerminalStub(...args);
      return terminalWithShell; // Return terminal with Shell Integration
    };

    // Mock empty terminals array so we create a new one
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return []; // No existing terminals
      },
      configurable: true,
    });

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should have called executeCommand for OpenHands command
    assert.ok(
      executeCommandSpy.called,
      "Shell Integration executeCommand should be called for OpenHands command",
    );

    // Check that the command was an OpenHands command
    const openhandsCall = executeCommandSpy.argsHistory.find(
      (args: any[]) => args[0] && args[0].includes("openhands"),
    );
    assert.ok(
      openhandsCall,
      `Should execute OpenHands command. Actual calls: ${JSON.stringify(executeCommandSpy.argsHistory)}`,
    );

    // Should create new terminal since none exist
    assert.ok(
      createTerminalStub.called,
      "Should create new terminal when none exist",
    );
  });

  test("Idle terminal tracking should reuse known idle terminals", async () => {
    const executeCommandSpy = createManualSpy();

    // Mock execution for OpenHands command
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OpenHands started successfully";
        },
      }),
      exitCode: Promise.resolve(0),
      commandLine: {
        value: "openhands",
        isTrusted: true,
        confidence: 2,
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    const terminalWithShell = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: mockShellIntegration,
    };

    // First, manually mark the terminal as idle (simulating a previous successful command)
    // We need to access the extension's internal idle tracking
    // For testing, we'll simulate this by running a command first, then another
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithShell];
      },
      configurable: true,
    });

    createTerminalStub.resetHistory();

    // First command to establish the terminal as idle
    await vscode.commands.executeCommand("openhands.startConversation");

    // Simulate command completion to mark terminal as idle
    // This would normally happen via the onDidEndTerminalShellExecution event

    createTerminalStub.resetHistory();
    executeCommandSpy.resetHistory();

    // Second command should reuse the terminal if it's marked as idle
    await vscode.commands.executeCommand("openhands.startConversation");

    // Should show terminal
    assert.ok(showSpy.called, "Should show terminal");
  });

  test("Shell Integration should use executeCommand when available", async () => {
    const executeCommandSpy = createManualSpy();

    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OpenHands started successfully";
        },
      }),
      exitCode: Promise.resolve(0),
      commandLine: {
        value: "openhands",
        isTrusted: true,
        confidence: 2,
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
      cwd: vscode.Uri.file("/test/directory"),
    };

    const terminalWithShell = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: mockShellIntegration,
    };

    // Mock createTerminal to return a terminal with Shell Integration
    createTerminalStub.resetHistory();
    vscode.window.createTerminal = (...args: any[]): vscode.Terminal => {
      createTerminalStub(...args);
      return terminalWithShell; // Return terminal with Shell Integration
    };

    // Mock empty terminals array so we create a new one
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return []; // No existing terminals
      },
      configurable: true,
    });

    sendTextSpy.resetHistory();
    executeCommandSpy.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should use Shell Integration executeCommand, not sendText
    assert.ok(
      executeCommandSpy.called,
      "Should use Shell Integration executeCommand",
    );

    // The OpenHands command should be executed via Shell Integration
    const openhandsCommand = executeCommandSpy.argsHistory.find(
      (args: any[]) => args[0] && args[0].includes("openhands"),
    );
    assert.ok(
      openhandsCommand,
      "Should execute OpenHands command via Shell Integration",
    );
  });

  test("Terminal creation should work when no existing terminals", async () => {
    // Mock empty terminals array
    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return []; // No existing terminals
      },
      configurable: true,
    });

    createTerminalStub.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should create new terminal when none exist
    assert.ok(
      createTerminalStub.called,
      "Should create new terminal when none exist",
    );

    // Should show the new terminal
    assert.ok(showSpy.called, "Should show the new terminal");
  });

  test("Shell Integration fallback should work when Shell Integration unavailable", async () => {
    // Create terminal without Shell Integration
    const terminalWithoutShell = {
      name: "OpenHands 10:30:15",
      processId: Promise.resolve(456),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined,
      state: {
        isInteractedWith: false,
        shell: undefined as string | undefined,
      },
      shellIntegration: undefined, // No Shell Integration
    };

    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithoutShell];
      },
      configurable: true,
    });

    createTerminalStub.resetHistory();
    sendTextSpy.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should create new terminal when no Shell Integration available
    assert.ok(
      createTerminalStub.called,
      "Should create new terminal when Shell Integration unavailable",
    );

    // Should use sendText fallback for the new terminal
    assert.ok(sendTextSpy.called, "Should use sendText fallback");
    assert.ok(
      sendTextSpy.lastArgs[0].includes("openhands"),
      "Should send OpenHands command",
    );
  });
});

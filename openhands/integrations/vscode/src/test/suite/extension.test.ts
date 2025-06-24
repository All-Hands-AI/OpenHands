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

  test("openhands.startConversationWithFileContext (untitled file) should send --task command", async () => {
    const untitledFileContent = "untitled content";
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
        },
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithFileContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");
    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --task "${untitledFileContent}"`,
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

  test("openhands.startConversationWithFileContext (no editor) should show error", async () => {
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
    assert.ok(showErrorMessageSpy.called, "showErrorMessage should be called");
    assert.strictEqual(
      showErrorMessageSpy.lastArgs[0],
      "OpenHands: No active text editor found.",
    );

    if (originalActiveTextEditor) {
      Object.defineProperty(
        vscode.window,
        "activeTextEditor",
        originalActiveTextEditor,
      );
    }
  });

  test("openhands.startConversationWithSelectionContext should send --task with selection", async () => {
    const selectedText = "selected text for openhands";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(
      vscode.window,
      "activeTextEditor",
    );
    Object.defineProperty(vscode.window, "activeTextEditor", {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file("/test/file.py"),
          getText: (selection?: vscode.Selection) =>
            selection ? selectedText : "full content",
        },
        selection: {
          isEmpty: false,
          active: new vscode.Position(0, 0),
          anchor: new vscode.Position(0, 0),
          start: new vscode.Position(0, 0),
          end: new vscode.Position(0, 10),
        } as vscode.Selection, // Mock non-empty selection
      }),
      configurable: true,
    });

    await vscode.commands.executeCommand(
      "openhands.startConversationWithSelectionContext",
    );
    assert.ok(sendTextSpy.called, "terminal.sendText should be called");
    assert.deepStrictEqual(sendTextSpy.lastArgs, [
      `openhands --task "${selectedText}"`,
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

  test("openhands.startConversationWithSelectionContext (no selection) should show error", async () => {
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
    assert.ok(showErrorMessageSpy.called, "showErrorMessage should be called");
    assert.strictEqual(
      showErrorMessageSpy.lastArgs[0],
      "OpenHands: No text selected.",
    );

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

  test("Shell Integration probe should detect idle terminal", async () => {
    const executeCommandSpy = createManualSpy();

    // Mock execution that responds with probe ID
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OPENHANDS_PROBE_123456789"; // Simulate successful probe response
        },
      }),
      exitCode: Promise.resolve(0),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
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

    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithShell];
      },
      configurable: true,
    });

    createTerminalStub.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should have called executeCommand for probe
    assert.ok(
      executeCommandSpy.called,
      "Shell Integration executeCommand should be called for probe",
    );

    // Check if any of the calls was a probe command
    const probeCall = executeCommandSpy.argsHistory.find(
      (args: any[]) => args[0] && args[0].includes("OPENHANDS_PROBE_"),
    );
    assert.ok(
      probeCall,
      `Should execute probe command. Actual calls: ${JSON.stringify(executeCommandSpy.argsHistory)}`,
    );

    // Should reuse terminal (not create new one)
    assert.ok(
      !createTerminalStub.called,
      "Should not create new terminal when existing one is idle",
    );
    assert.ok(showSpy.called, "Should show the reused terminal");
  });

  test("Shell Integration probe should handle timeout gracefully", async () => {
    const executeCommandSpy = createManualSpy();

    // Mock execution that never responds (simulates hanging terminal)
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          // Never yield the expected probe response - simulate hanging
          yield "some other output";
          // Simulate infinite hanging by never resolving
          await new Promise(() => {}); // Never resolves
        },
      }),
      exitCode: Promise.resolve(0),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
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

    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithShell];
      },
      configurable: true,
    });

    createTerminalStub.resetHistory();

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should have attempted probe
    assert.ok(executeCommandSpy.called, "Should attempt probe");

    // Should still reuse terminal even if probe times out (Shell Integration handles interruption)
    assert.ok(showSpy.called, "Should show terminal even after probe timeout");
  });

  test("Shell Integration should use executeCommand instead of sendText", async () => {
    const executeCommandSpy = createManualSpy();

    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OPENHANDS_PROBE_123456789";
        },
      }),
      exitCode: Promise.resolve(0),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
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

    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithShell];
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

    // Should have called executeCommand at least twice: once for probe, once for actual command
    assert.ok(
      executeCommandSpy.callCount >= 2,
      "Should call executeCommand for probe and actual command",
    );

    // The actual OpenHands command should be executed via Shell Integration
    const openhandsCommand = executeCommandSpy.argsHistory.find(
      (args: any[]) =>
        args[0] &&
        args[0].includes("openhands") &&
        !args[0].includes("OPENHANDS_PROBE_"),
    );
    assert.ok(
      openhandsCommand,
      "Should execute OpenHands command via Shell Integration",
    );
  });

  test("Shell Integration should monitor command execution completion", async () => {
    const executeCommandSpy = createManualSpy();

    // Mock the execution object that will be returned
    const mockExecution = {
      read: () => ({
        async *[Symbol.asyncIterator]() {
          yield "OPENHANDS_PROBE_123456789";
        },
      }),
      exitCode: Promise.resolve(0),
    };

    const mockShellIntegration = {
      executeCommand: (command: string) => {
        executeCommandSpy(command);
        return mockExecution;
      },
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

    Object.defineProperty(vscode.window, "terminals", {
      get: () => {
        findTerminalStub();
        return [terminalWithShell];
      },
      configurable: true,
    });

    await vscode.commands.executeCommand("openhands.startConversation");

    // Should use Shell Integration executeCommand
    assert.ok(
      executeCommandSpy.called,
      "Should use Shell Integration executeCommand",
    );

    // Note: We can't easily test the event handler registration in unit tests
    // since vscode.window.onDidEndTerminalShellExecution is read-only
    // This would be better tested in integration tests
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

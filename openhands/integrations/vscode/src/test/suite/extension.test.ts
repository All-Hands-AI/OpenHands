import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Test Suite', () => {
  let mockTerminal: vscode.Terminal;
  let sendTextSpy: any; // Manual spy, using 'any' type
  let showSpy: any;     // Manual spy
  let createTerminalStub: any; // Manual stub
  let findTerminalStub: any;   // Manual spy
  let showErrorMessageSpy: any; // Manual spy

  // It's better to use a proper mocking library like Sinon.JS for spies and stubs.
  // For now, we'll use a simplified manual approach for spies.
  const createManualSpy = () => {
    const spy: any = (...args: any[]) => { // eslint-disable-line @typescript-eslint/no-explicit-any
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
      name: 'OpenHands',
      processId: Promise.resolve(123),
      sendText: sendTextSpy as any,
      show: showSpy as any,
      hide: () => {},
      dispose: () => {},
      creationOptions: {},
      exitStatus: undefined, // Added to satisfy Terminal interface
      state: { isInteractedWith: false, shell: undefined as string | undefined }, // Added shell property
      shellIntegration: undefined // Added to satisfy Terminal interface
    };

    // Store original functions
    const _originalCreateTerminal = vscode.window.createTerminal;
    const _originalTerminalsDescriptor = Object.getOwnPropertyDescriptor(vscode.window, 'terminals');
    const _originalShowErrorMessage = vscode.window.showErrorMessage;

    // Stub vscode.window.createTerminal
    createTerminalStub = createManualSpy();
    vscode.window.createTerminal = (...args: any[]): vscode.Terminal => {
        createTerminalStub(...args); // Call the spy with whatever arguments it received
        return mockTerminal;         // Return the mock terminal
    };

    // Stub vscode.window.terminals
    findTerminalStub = createManualSpy(); // To track if vscode.window.terminals getter is accessed
    Object.defineProperty(vscode.window, 'terminals', {
      get: () => {
        findTerminalStub();
        // Default to returning the mockTerminal, can be overridden in specific tests
        return [mockTerminal];
      },
      configurable: true
    });

    vscode.window.showErrorMessage = showErrorMessageSpy as any;

    // Teardown logic to restore original functions
    teardown(() => {
      vscode.window.createTerminal = _originalCreateTerminal;
      if (_originalTerminalsDescriptor) {
        Object.defineProperty(vscode.window, 'terminals', _originalTerminalsDescriptor);
      } else {
        // If it wasn't originally defined, delete it to restore to that state
        delete (vscode.window as any).terminals;
      }
      vscode.window.showErrorMessage = _originalShowErrorMessage;
    });
  });


  test('Extension should be present and activate', async () => {
    const extension = vscode.extensions.getExtension('openhands.openhands-vscode');
    assert.ok(extension, 'Extension should be found (check publisher.name in package.json)');
    if (!extension.isActive) {
      await extension.activate();
    }
    assert.ok(extension.isActive, 'Extension should be active');
  });

  test('Commands should be registered', async () => {
    const extension = vscode.extensions.getExtension('openhands.openhands-vscode');
    if (extension && !extension.isActive) {
      await extension.activate();
    }
    const commands = await vscode.commands.getCommands(true);
    const expectedCommands = [
      'openhands.startConversation',
      'openhands.startConversationWithFileContext',
      'openhands.startConversationWithSelectionContext'
    ];
    for (const cmd of expectedCommands) {
      assert.ok(commands.includes(cmd), `Command '${cmd}' should be registered`);
    }
  });

  test('openhands.startConversation should send correct command to terminal', async () => {
    findTerminalStub.resetHistory(); // Reset for this specific test path if needed
    Object.defineProperty(vscode.window, 'terminals', { get: () => { findTerminalStub(); return []; }, configurable: true }); // Simulate no existing terminal

    await vscode.commands.executeCommand('openhands.startConversation');

    assert.ok(createTerminalStub.called, 'vscode.window.createTerminal should be called');
    assert.ok(showSpy.called, 'terminal.show should be called');
    assert.deepStrictEqual(sendTextSpy.lastArgs, ['openhands', true], 'Correct command sent to terminal');
  });

  test('openhands.startConversationWithFileContext (saved file) should send --file command', async () => {
    const testFilePath = '/test/file.py';
    // Mock activeTextEditor for a saved file
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(vscode.window, 'activeTextEditor');
    Object.defineProperty(vscode.window, 'activeTextEditor', {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file(testFilePath),
          fsPath: testFilePath, // fsPath is often used
          getText: () => 'file content' // Not used for saved files but good to have
        }
      }),
      configurable: true
    });

    await vscode.commands.executeCommand('openhands.startConversationWithFileContext');
    assert.ok(sendTextSpy.called, 'terminal.sendText should be called');
    assert.deepStrictEqual(sendTextSpy.lastArgs, [`openhands --file ${testFilePath.includes(' ') ? `"${testFilePath}"` : testFilePath}`, true]);

    // Restore activeTextEditor
    if (originalActiveTextEditor) {
      Object.defineProperty(vscode.window, 'activeTextEditor', originalActiveTextEditor);
    }
  });

  test('openhands.startConversationWithFileContext (untitled file) should send --task command', async () => {
    const untitledFileContent = "untitled content";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(vscode.window, 'activeTextEditor');
    Object.defineProperty(vscode.window, 'activeTextEditor', {
      get: () => ({
        document: {
          isUntitled: true,
          uri: vscode.Uri.parse('untitled:Untitled-1'),
          getText: () => untitledFileContent
        }
      }),
      configurable: true
    });

    await vscode.commands.executeCommand('openhands.startConversationWithFileContext');
    assert.ok(sendTextSpy.called, 'terminal.sendText should be called');
    assert.deepStrictEqual(sendTextSpy.lastArgs, [`openhands --task "${untitledFileContent}"`, true]);

    if (originalActiveTextEditor) {
      Object.defineProperty(vscode.window, 'activeTextEditor', originalActiveTextEditor);
    }
  });

  test('openhands.startConversationWithFileContext (no editor) should show error', async () => {
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(vscode.window, 'activeTextEditor');
    Object.defineProperty(vscode.window, 'activeTextEditor', { get: () => undefined, configurable: true });

    await vscode.commands.executeCommand('openhands.startConversationWithFileContext');
    assert.ok(showErrorMessageSpy.called, 'showErrorMessage should be called');
    assert.strictEqual(showErrorMessageSpy.lastArgs[0], 'OpenHands: No active text editor found.');

    if (originalActiveTextEditor) {
      Object.defineProperty(vscode.window, 'activeTextEditor', originalActiveTextEditor);
    }
  });

  test('openhands.startConversationWithSelectionContext should send --task with selection', async () => {
    const selectedText = "selected text for openhands";
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(vscode.window, 'activeTextEditor');
    Object.defineProperty(vscode.window, 'activeTextEditor', {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file('/test/file.py'),
          getText: (selection?: vscode.Selection) => selection ? selectedText : "full content"
        },
        selection: { isEmpty: false, active: new vscode.Position(0,0), anchor: new vscode.Position(0,0), start: new vscode.Position(0,0), end: new vscode.Position(0,10) } as vscode.Selection // Mock non-empty selection
      }),
      configurable: true
    });

    await vscode.commands.executeCommand('openhands.startConversationWithSelectionContext');
    assert.ok(sendTextSpy.called, 'terminal.sendText should be called');
    assert.deepStrictEqual(sendTextSpy.lastArgs, [`openhands --task "${selectedText}"`, true]);

    if (originalActiveTextEditor) {
      Object.defineProperty(vscode.window, 'activeTextEditor', originalActiveTextEditor);
    }
  });

  test('openhands.startConversationWithSelectionContext (no selection) should show error', async () => {
    const originalActiveTextEditor = Object.getOwnPropertyDescriptor(vscode.window, 'activeTextEditor');
    Object.defineProperty(vscode.window, 'activeTextEditor', {
      get: () => ({
        document: {
          isUntitled: false,
          uri: vscode.Uri.file('/test/file.py'),
          getText: () => "full content"
        },
        selection: { isEmpty: true } as vscode.Selection // Mock empty selection
      }),
      configurable: true
    });

    await vscode.commands.executeCommand('openhands.startConversationWithSelectionContext');
    assert.ok(showErrorMessageSpy.called, 'showErrorMessage should be called');
    assert.strictEqual(showErrorMessageSpy.lastArgs[0], 'OpenHands: No text selected.');

    if (originalActiveTextEditor) {
      Object.defineProperty(vscode.window, 'activeTextEditor', originalActiveTextEditor);
    }
  });

});

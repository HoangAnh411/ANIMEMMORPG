# AI Agent Guidelines - AnimeMMORPG

This repository is an Unreal Engine 5.8 project configured with the **Model Context Protocol (MCP)** server for automation, editor manipulation, and testing.

---

## 1. Unreal Engine MCP Server (`unreal-mcp`)

- **Server endpoint:** `http://127.0.0.1:8000/mcp`
- **MCP Meta-Tools available:**
  - `list_toolsets`: Lists all registered toolsets.
  - `describe_toolset`: Retrieves schemas and parameter definitions for a toolset.
  - `call_tool`: Calls a specific tool within a toolset.

---

## 2. Project Custom Toolset (`TestRunnerTools`)

Toolset name: **`test_runner.toolsets.test_runner.TestRunnerTools`**

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `run_automation_tests` | `{"filter": "<FilterString>"}` | Triggers automation tests by filter expression (e.g. `"AnimeMMORPG.U00.Foundation"`). |
| `stop_automation_tests` | `{}` | Cancels/stops any actively executing or queued automation tests. |
| `live_coding_compile` | `{}` | Triggers Live Coding compilation (`LiveCoding.Compile`) without manual hotkeys. |
| `execute_console_command` | `{"command": "<CommandString>"}` | Executes any console command in Unreal Editor (e.g. `"RestartLevel"`, `"stat fps"`, `"r.SetRes 1920x1080"`). |
| `save_all_dirty_assets` | `{}` | Saves all modified (dirty) packages, maps, and content assets to disk. |
| `save_current_level` | `{}` | Saves the currently active level map asset to disk. |
| `get_editor_summary` | `{}` | Returns JSON summary of active level, actor count, selected actors, and status. |

---

## 3. Running Automation Tests via MCP

Whenever asked to run automation tests, use the following workflow:

### Step 1: Trigger Tests
Call MCP tool `call_tool` with:
- **`toolset_name`**: `"test_runner.toolsets.test_runner.TestRunnerTools"`
- **`tool_name`**: `"run_automation_tests"`
- **`arguments`**:
  ```json
  {
    "filter": "AnimeMMORPG.U00.Foundation"
  }
  ```
  *(Replace `"AnimeMMORPG.U00.Foundation"` with the target test name or prefix expression, e.g. `"AnimeMMORPG"` for all project tests).*

### Step 2: Read Test Results
Call MCP tool `call_tool` with:
- **`toolset_name`**: `"EditorToolset.LogsToolset"`
- **`tool_name`**: `"GetLogEntries"`
- **`arguments`**:
  ```json
  {
    "pattern": "Test Completed|Automation Test Queue Empty|No automation tests matched",
    "category": "",
    "maxEntries": 50
  }
  ```

### Step 3: Report Results
Parse the log lines and report:
- Total tests executed.
- Result for each test: `Success` (Passed) or `Failed`.
- Error messages if any test failed.

---

## 4. Compiling C++ Changes via Live Coding (`live_coding_compile`)

When C++ code is modified, use `live_coding_compile` to trigger compilation inside the running Editor without manually pressing hotkeys:

### Step-by-Step Workflow:
1. **Get Log Category:** Call `EditorToolset.LogsToolset.GetLogCategories` with `{"filter": "LiveCoding"}` to confirm category name (typically `"LogLiveCoding"`).
2. **Trigger Compilation:** Call `test_runner.toolsets.test_runner.TestRunnerTools.live_coding_compile` with `{}`.
3. **Poll Results:** Wait 3-5 seconds, then call `EditorToolset.LogsToolset.GetLogEntries` with:
   ```json
   {
     "category": "LogLiveCoding",
     "pattern": "Live coding succeeded|Failed to compile|Error:|succeeded",
     "maxEntries": 50
   }
   ```
   Repeat polling if compilation is still in progress.
4. **Report Results:** Report compilation outcome using exact compiler output from the logs (do NOT guess log lines). If compilation failed, extract and report the specific error messages and file line numbers.
5. **Header/UCLASS/UPROPERTY Warning:** If the code changes introduce or modify UCLASS, UPROPERTY, UFUNCTION, USTRUCT, or new headers, warn the user that Live Coding cannot patch reflection/header layout changes and that a full build via UnrealBuildTool (UBT) and Editor restart is required.

---

## 5. Alternative Advanced Test Controller (`AutomationTestToolset`)

For fine-grained test listing or stopping tests:
- **`toolset_name`**: `"AutomationTestToolset.AutomationTestToolset"`
- **Tools**:
  - `DiscoverTests`: `{"bForceRediscover": false}` (must run once per session before listing).
  - `ListTests`: `{"nameFilter": "<Substring>", "tagFilter": "", "limit": 200}`
  - `RunTests`: `{"testNames": ["<FullPath1>", ...]}`
  - `RunTestsByFilter`: `{"filterExpression": "StartsWith:AnimeMMORPG"}`
  - `GetTestStatus`: Retrieves lightweight completion/pass/fail counts.
  - `GetTestResults`: Retrieves detailed per-test failure messages.
  - `StopTests`: Aborts currently running tests.

---

## 6. Important Troubleshooting & Caveats

1. **Unfocused Editor Window (FPS Throttle):**
   - If *"Use Less CPU when in Background"* is enabled in Editor Preferences, the Editor throttles background framerate to ~3 FPS.
   - Automation runner queues tests with `FWaitForInteractiveFrameRate: Starting wait for framerate of >= 10 FPS`.
   - Ensure `bThrottleCPUWhenNotForeground` is set to `false` in `EditorPerformanceSettings` so tests run automatically without needing manual focus.

Pawn metrics are deferred to U01. The current TestRunner exposes no PIE pawn metrics tool; do not use Editor world as evidence of a PIE pawn. Project toolset dependencies are explicit; do not enable AllToolsets to hide missing tools or GameFeatures warnings.

# Copyright Epic Games, Inc. All Rights Reserved.

import json
import unreal
import toolset_registry


@unreal.uclass()
class TestRunnerTools(unreal.ToolsetDefinition):
    """Provides tools for running Unreal Engine automation tests, Live Coding, and editor inspection."""

    @toolset_registry.tool_call
    @staticmethod
    def run_automation_tests(filter: str) -> str:
        """Triggers automation tests matching the specified filter expression.

        This tool initiates the automation test run in the Unreal Editor
        and returns immediately without waiting for test completion. Test progress
        and results can be monitored via the Unreal Editor Output Log.

        Args:
            filter: Substring or prefix filter for the automation tests to run (e.g. 'AnimeMMORPG.U00.Foundation').

        Returns:
            A confirmation string indicating that the test execution command was issued.
        """
        unreal.SystemLibrary.execute_console_command(None, f"Automation RunTests {filter}")
        return f"Triggered automation tests with filter: {filter}"

    @toolset_registry.tool_call
    @staticmethod
    def stop_automation_tests() -> str:
        """Stops and cancels any currently executing or queued automation tests.

        Returns:
            A confirmation string indicating that the stop command was issued.
        """
        unreal.SystemLibrary.execute_console_command(None, "Automation StopTests")
        return "Requested stop for active automation tests."

    @toolset_registry.tool_call
    @staticmethod
    def live_coding_compile() -> str:
        """Triggers Live Coding compilation in the Unreal Editor.

        This tool only initiates the Live Coding compilation process and returns
        immediately; it does not wait for compilation to complete. The compilation
        progress and result (success or failure) must be read from the Editor Output Log.

        Returns:
            A confirmation string indicating that Live Coding compilation was triggered.
        """
        unreal.SystemLibrary.execute_console_command(None, "LiveCoding.Compile")
        return "Triggered Live Coding compilation."

    @toolset_registry.tool_call
    @staticmethod
    def execute_console_command(command: str) -> str:
        """Executes an arbitrary console command in the Unreal Editor.

        Args:
            command: The console command string to execute (e.g. 'stat fps', 'RestartLevel', 'r.SetRes 1920x1080').

        Returns:
            A confirmation string indicating that the console command was issued.
        """
        unreal.SystemLibrary.execute_console_command(None, command)
        return f"Executed console command: {command}"

    @toolset_registry.tool_call
    @staticmethod
    def save_all_dirty_assets() -> bool:
        """Saves all unsaved (dirty) packages, maps, and content assets to disk.

        Returns:
            True if all dirty packages were saved successfully, False otherwise.
        """
        return unreal.EditorLoadingAndSavingUtils.save_dirty_packages(save_map_packages=True, save_content_packages=True)

    @toolset_registry.tool_call
    @staticmethod
    def save_current_level() -> bool:
        """Saves the currently active level map asset to disk.

        Returns:
            True if the current level was saved successfully, False otherwise.
        """
        return unreal.EditorLevelLibrary.save_current_level()

    @toolset_registry.tool_call
    @staticmethod
    def get_editor_summary() -> str:
        """Retrieves a summary of the active Unreal Editor state.

        Provides the current level path, total actor count in the level,
        currently selected actors, and PIE (Play-In-Editor) status.

        Returns:
            A JSON-formatted string with the editor state summary.
        """
        world = unreal.EditorLevelLibrary.get_editor_world()
        world_path = world.get_path_name() if world else "None"
        actors = unreal.EditorLevelLibrary.get_all_level_actors() if world else []
        selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors() if world else []

        summary = {
            "current_level": world_path,
            "total_actors": len(actors),
            "selected_actors_count": len(selected_actors),
            "selected_actors": [a.get_actor_label() for a in selected_actors[:10]],
        }
        return json.dumps(summary)

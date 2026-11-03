// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class AnimeMMORPG : ModuleRules
{
	public AnimeMMORPG(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { "SlateCore", "ApplicationCore", "Json" });

		PublicIncludePaths.AddRange(new string[] {
			"AnimeMMORPG",
			"AnimeMMORPG/Variant_Platforming",
			"AnimeMMORPG/Variant_Platforming/Animation",
			"AnimeMMORPG/Variant_Combat",
			"AnimeMMORPG/Variant_Combat/AI",
			"AnimeMMORPG/Variant_Combat/Animation",
			"AnimeMMORPG/Variant_Combat/Gameplay",
			"AnimeMMORPG/Variant_Combat/Interfaces",
			"AnimeMMORPG/Variant_Combat/UI",
			"AnimeMMORPG/Variant_SideScrolling",
			"AnimeMMORPG/Variant_SideScrolling/AI",
			"AnimeMMORPG/Variant_SideScrolling/Gameplay",
			"AnimeMMORPG/Variant_SideScrolling/Interfaces",
			"AnimeMMORPG/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}

#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "U01AnimationEditor.generated.h"

UCLASS()
class ANIMEMMORPG_API UU01AnimationEditor : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Narrow asset-authoring entry point; refuses the original workspace, editor only.
    UFUNCTION(BlueprintCallable, Category="U01|Authoring")
    static FString BuildDAssets();
    UFUNCTION(BlueprintCallable, Category="U01|Authoring")
    static FString FinalizeDBlendSpace();
    UFUNCTION(BlueprintCallable, Category="U01|Authoring")
    static FString InspectDHand(const FString& OutputDirectory);
    UFUNCTION(BlueprintCallable, Category="U01|Authoring")
    static FString ReviseDAssets(const FString& ConfigFile);
    UFUNCTION(BlueprintCallable, Category="U01|Authoring")
    static FString ReviseDCarry(const FString& ConfigFile);
};

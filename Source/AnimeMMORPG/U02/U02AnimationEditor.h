#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "U02AnimationEditor.generated.h"

UCLASS()
class ANIMEMMORPG_API UU02AnimationEditor : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="U02|Authoring") static FString BuildCAssets();
};

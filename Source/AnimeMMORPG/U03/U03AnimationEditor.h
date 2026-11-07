#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "U03AnimationEditor.generated.h"
UCLASS()
class ANIMEMMORPG_API UU03AnimationEditor : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="U03|Authoring") static FString BuildA1Assets();
};

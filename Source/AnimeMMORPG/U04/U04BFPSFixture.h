#pragma once
#include "CoreMinimal.h"
class UWorld;
class AU01Character;
class FJsonObject;
// Development opt-in evidence only. No gameplay input or timing policy lives here.
namespace U04B
{
bool Enabled(const UWorld* World);
void BeginWorld(UWorld& World);
void EndWorld(UWorld* World);
void Event(UWorld* World, const TCHAR* Kind, TSharedRef<FJsonObject> Data);
void DodgeCommit(AU01Character* Pawn, double At, bool End);
}

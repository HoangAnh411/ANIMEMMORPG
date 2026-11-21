#pragma once
#include "CoreMinimal.h"
class UWorld;
class FJsonObject;
namespace U04C1
{
// Owned by one collision world. Integer increments only inside an explicit window.
struct FCounters
{
    bool Enabled=false,Active=false;
    uint64 Visits=0,Geometry=0,Occlusion=0,Candidates=0,Confirmed=0,Suppressed=0,Intervals=0,Actions=0;
};
bool Enabled(const UWorld* World);
void BeginWorld(UWorld& World);
void EndWorld(UWorld* World);
void Event(UWorld* World,const TCHAR* Kind,TSharedRef<FJsonObject> Data);
}

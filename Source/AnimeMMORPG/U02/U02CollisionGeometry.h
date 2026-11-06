#pragma once
#include "CoreMinimal.h"

namespace AnimeMMORPG::U02
{
struct FTriangle { FVector A,B,C; };
struct FContactRange { bool bHit=false; double Begin=0,End=0; };
// All fractions refer to the ORIGINAL collision snapshot interval, not a re-based frame.
FContactRange SphereAttackContact(FVector Feet0,FVector Feet1,double LockedYaw,
    FVector Center0,FVector Center1,double Radius,double BeginAlpha,double EndAlpha);
FVector AttackCenter(FVector Feet,double Yaw);
FVector SphereNearest(FVector Origin,FVector Center,double Radius);
bool SegmentTriangleClosed(FVector From,FVector To,const FTriangle& Triangle);
// Partition at all visibility topology changes (edge/plane/near-sphere quartic roots).
// The predicate includes initial-solid containment and actual world query validation.
TOptional<double> FirstVisible(FVector Origin0,FVector Origin1,FVector Center0,FVector Center1,
    double Radius,FContactRange Contact,const TArray<FTriangle>& Triangles,
    TFunctionRef<bool(double)> IsUnobstructed);
void AddBoxTriangles(const FTransform& Transform,FVector Half,TArray<FTriangle>& Out);
}

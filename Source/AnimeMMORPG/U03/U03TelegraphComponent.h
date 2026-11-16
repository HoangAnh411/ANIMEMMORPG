#pragma once
#include "CoreMinimal.h"
#include "Components/PrimitiveComponent.h"
#include "U03TelegraphComponent.generated.h"

struct FU03TelegraphSegment
{
    FVector A,B;float Width=1;
    bool operator==(const FU03TelegraphSegment& Other) const {return A==Other.A&&B==Other.B&&Width==Other.Width;}
};
// Small production world primitive, not DrawDebug/Canvas or the debug-only PDI.
// Vertices are world-space confirmed sword geometry; renderer depth-tests pixels.
UCLASS(Transient)
class ANIMEMMORPG_API UU03TelegraphComponent : public UPrimitiveComponent
{
    GENERATED_BODY()
public:
    UU03TelegraphComponent();
    static TArray<FU03TelegraphSegment> SwordSegments(FVector Feet,double Yaw,float Width);
    void SetSegments(TArray<FU03TelegraphSegment> In);
    const TArray<FU03TelegraphSegment>& GetSegments() const {return Segments;}
    virtual FPrimitiveSceneProxy* CreateSceneProxy() override;
    virtual FBoxSphereBounds CalcBounds(const FTransform& LocalToWorld) const override;
private:
    TArray<FU03TelegraphSegment> Segments;
};

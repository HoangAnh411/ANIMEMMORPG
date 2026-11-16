#include "U03TelegraphComponent.h"
#include "PrimitiveSceneProxy.h"
#include "PrimitiveViewRelevance.h"
#include "MeshElementCollector.h"
#include "SceneManagement.h"

namespace {
class FU03TelegraphProxy final : public FPrimitiveSceneProxy
{
    const TArray<FU03TelegraphSegment> Segments;
public:
    explicit FU03TelegraphProxy(const UU03TelegraphComponent* C):FPrimitiveSceneProxy(C),Segments(C->GetSegments()){bWillEverBeLit=false;}
    SIZE_T GetTypeHash() const override {static size_t Type;return reinterpret_cast<size_t>(&Type);}
    uint32 GetMemoryFootprint() const override {return sizeof(*this)+Segments.GetAllocatedSize();}
    FPrimitiveViewRelevance GetViewRelevance(const FSceneView* View) const override
    {FPrimitiveViewRelevance R;R.bDrawRelevance=IsShown(View);R.bDynamicRelevance=true;R.bNormalTranslucency=true;R.bSeparateTranslucency=true;return R;}
    void GetDynamicMeshElements(const TArray<const FSceneView*>& Views,const FSceneViewFamily&,uint32 VisibilityMap,FMeshElementCollector& Collector) const override
    {
        for(int32 V=0;V<Views.Num();++V)if(VisibilityMap&(1<<V))
            for(const auto& S:Segments)
                // Regular world PDI, SDPG_World, zero depth bias, no screen-space
                // or depth-test bypass. Occluded portions are rejected per pixel.
                Collector.GetPDI(V)->DrawLine(S.A,S.B,FLinearColor::White,SDPG_World,S.Width,0,false);
    }
};
}
UU03TelegraphComponent::UU03TelegraphComponent()
{
    PrimaryComponentTick.bCanEverTick=false;SetCollisionEnabled(ECollisionEnabled::NoCollision);SetGenerateOverlapEvents(false);SetCanEverAffectNavigation(false);
    CastShadow=false;bUseAsOccluder=false;
}
TArray<FU03TelegraphSegment> UU03TelegraphComponent::SwordSegments(FVector Feet,double Yaw,float Width)
{
    const FRotator R(0,Yaw,0);FVector V[8];TArray<FU03TelegraphSegment> Out;
    for(int32 I=0;I<8;++I)V[I]=Feet+R.RotateVector(FVector((I&1)?200:0,(I&2)?60:-60,(I&4)?180:0));
    for(int32 I=0;I<8;++I)for(int32 Bit:{1,2,4})if(!(I&Bit))Out.Add({V[I],V[I|Bit],Width});
    const FVector A=Feet+FVector(0,0,190),B=A+R.Vector()*180;
    Out.Add({A,B,2});Out.Add({B,B-R.RotateVector(FVector(25,15,0)),2});Out.Add({B,B-R.RotateVector(FVector(25,-15,0)),2});return Out;
}
void UU03TelegraphComponent::SetSegments(TArray<FU03TelegraphSegment> In)
{if(Segments==In)return;Segments=MoveTemp(In);UpdateBounds();MarkRenderStateDirty();}
FPrimitiveSceneProxy* UU03TelegraphComponent::CreateSceneProxy()
{return Segments.IsEmpty()?nullptr:new FU03TelegraphProxy(this);}
FBoxSphereBounds UU03TelegraphComponent::CalcBounds(const FTransform&) const
{FBox Box(ForceInit);for(const auto& S:Segments){Box+=S.A;Box+=S.B;}return Box.IsValid?FBoxSphereBounds(Box.ExpandBy(5)):FBoxSphereBounds(FVector::ZeroVector,FVector(1),1);}

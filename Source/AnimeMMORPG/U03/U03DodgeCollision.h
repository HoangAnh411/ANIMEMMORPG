#pragma once
#include "CoreMinimal.h"
namespace AnimeMMORPG::U03
{
// Continuous relative motion of upright capsules; split where the closest
// points switch between cylinder and spherical caps. Geometry tolerance only,
// never a tolerance on action/buffer deadlines.
inline TOptional<double> CapsuleContact(FVector A,FVector EndA,FVector B,FVector EndB,double Radius,double HalfSegments)
{
    const FVector P=A-B,V=(EndA-A)-(EndB-B);TArray<double> Cuts{0.,1.};
    if(V.Z!=0)for(double Z:{-HalfSegments,HalfSegments}){const double T=(Z-P.Z)/V.Z;if(T>0&&T<1)Cuts.Add(T);}
    Cuts.Sort();
    for(int32 I=1;I<Cuts.Num();++I)
    {
        const double L=Cuts[I-1],R=Cuts[I],Mid=(L+R)*.5;FVector X=P,D=V;
        const double Z=P.Z+Mid*V.Z;
        if(Z>HalfSegments)X.Z-=HalfSegments;else if(Z<-HalfSegments)X.Z+=HalfSegments;else X.Z=D.Z=0;
        const FVector At=X+D*L;const double C=At.SizeSquared()-Radius*Radius,Beta=2*FVector::DotProduct(At,D),Alpha=D.SizeSquared();
        if(C<-.000001 || (C<=.000001&&Beta<0))return L;
        if(Alpha==0)continue;
        const double Discriminant=Beta*Beta-4*Alpha*C;if(Discriminant<0)continue;
        const double T=(-Beta-FMath::Sqrt(Discriminant))/(2*Alpha);
        if(T>0&&L+T<=R)return L+T;
    }
    return {};
}
}

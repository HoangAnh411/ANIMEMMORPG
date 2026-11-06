#include "U02CollisionGeometry.h"
#include <cmath>

namespace AnimeMMORPG::U02
{
namespace
{
using FPoly=TArray<double>;
double Eval(const FPoly& P,double T) { double V=0;for(int I=P.Num()-1;I>=0;--I)V=V*T+P[I];return V; }
FPoly Mul(const FPoly& A,const FPoly& B)
{
    FPoly R;R.Init(0,A.Num()+B.Num()-1);
    for(int I=0;I<A.Num();++I)for(int J=0;J<B.Num();++J)R[I+J]+=A[I]*B[J];return R;
}
void Roots(FPoly P,double Lo,double Hi,TArray<double>& Out)
{
    double Scale=0;for(double C:P)Scale=FMath::Max(Scale,FMath::Abs(C));if(Scale==0)return;
    for(double& C:P)C/=Scale;
    while(P.Num()>1 && P.Last()==0)P.Pop();
    if(P.Num()<2)return;
    if(P.Num()==2){double T=-P[0]/P[1];if(T>=Lo&&T<=Hi)Out.Add(T);return;}
    FPoly D;for(int I=1;I<P.Num();++I)D.Add(I*P[I]);
    TArray<double> Cuts{Lo,Hi};Roots(D,Lo,Hi,Cuts);Cuts.Sort();
    // Geometric root residual only; no gameplay timestamp/window is expanded.
    for(double T:Cuts)if(FMath::Abs(Eval(P,T))<1.e-12)Out.Add(T);
    for(int I=1;I<Cuts.Num();++I)
    {
        double A=Cuts[I-1],B=Cuts[I],FA=Eval(P,A),FB=Eval(P,B);
        if((FA<0)==(FB<0)||FA==0||FB==0)continue;
        for(int K=0;K<96;++K)
        {
            double M=A+(B-A)*.5;if(M==A||M==B)break;double FM=Eval(P,M);
            if(FM==0){A=B=M;break;}if((FM<0)==(FA<0)){A=M;FA=FM;}else B=M;
        }
        Out.Add(A+(B-A)*.5);
    }
}
}
FVector AttackCenter(FVector Feet,double Yaw) { return Feet+FRotator(0,Yaw,0).Quaternion().GetNormalized().RotateVector(FVector(100,0,90)); }
FVector SphereNearest(FVector Origin,FVector Center,double Radius)
{ FVector D=Origin-Center;return D.SizeSquared()<=Radius*Radius?Origin:Center+D.GetSafeNormal()*Radius; }
FContactRange SphereAttackContact(FVector F0,FVector F1,double Yaw,FVector C0,FVector C1,double R,double Lo,double Hi)
{
    FContactRange Out;if(R<0||!FMath::IsFinite(R)||Lo>Hi)return Out;
    const FQuat Q=FRotator(0,Yaw,0).Quaternion().GetNormalized();
    FVector P=Q.UnrotateVector(C0-AttackCenter(F0,Yaw));
    FVector V=Q.UnrotateVector((C1-C0)-(F1-F0));const FVector H(100+1.e-7,60+1.e-7,90+1.e-7);
    TArray<double> Cuts{Lo,Hi};
    for(int I=0;I<3;++I)if(V[I]!=0)for(double Sign:{-1.,1.})
    {double T=(Sign*H[I]-P[I])/V[I];if(T>Lo&&T<Hi)Cuts.Add(T);}
    Cuts.Sort();double First=TNumericLimits<double>::Max(),Last=-First;
    auto Inside=[&](double T){FVector X=P+V*T;double D=0;for(int I=0;I<3;++I)D+=FMath::Square(FMath::Max(0.,FMath::Abs(X[I])-H[I]));return D<=R*R;};
    for(double T:Cuts)if(Inside(T)){First=FMath::Min(First,T);Last=FMath::Max(Last,T);}
    for(int K=1;K<Cuts.Num();++K)
    {
        double A=Cuts[K-1],B=Cuts[K],M=(A+B)*.5,AA=0,BB=0,CC=-R*R;
        for(int I=0;I<3;++I)
        {
            double X=P[I]+V[I]*M;if(FMath::Abs(X)<=H[I])continue;
            double Offset=P[I]-(X<0?-H[I]:H[I]);AA+=V[I]*V[I];BB+=2*Offset*V[I];CC+=Offset*Offset;
        }
        if(AA==0){if(CC>0)continue;}
        else
        {
            double Disc=BB*BB-4*AA*CC;if(Disc<0)continue;
            double S=FMath::Sqrt(Disc);double X=(-BB-S)/(2*AA),Y=(-BB+S)/(2*AA);
            A=FMath::Max(A,X);B=FMath::Min(B,Y);if(A>B)continue;
        }
        First=FMath::Min(First,A);Last=FMath::Max(Last,B);
    }
    if(First<=Last){Out.bHit=true;Out.Begin=First;Out.End=Last;}return Out;
}
bool SegmentTriangleClosed(FVector O,FVector End,const FTriangle& T)
{
    const FVector E=T.B-T.A,F=T.C-T.A,N=FVector::CrossProduct(E,F),D=End-O;
    const double NS=N.Size();if(NS==0)return false;
    constexpr double Tol=1.e-7; // cm, closed geometric boundary only
    double Den=FVector::DotProduct(N,D),Num=FVector::DotProduct(N,T.A-O);
    auto In=[&](FVector P){return FVector::DotProduct(FVector::CrossProduct(T.B-T.A,P-T.A),N)>=-Tol*NS
        &&FVector::DotProduct(FVector::CrossProduct(T.C-T.B,P-T.B),N)>=-Tol*NS
        &&FVector::DotProduct(FVector::CrossProduct(T.A-T.C,P-T.C),N)>=-Tol*NS;};
    if(Den!=0)
    {double U=Num/Den;return U>=0&&U<=1&&In(O+D*U);}
    if(FMath::Abs(Num)>Tol*NS)return false;
    double A=0,B=1;
    const FVector Verts[]={T.A,T.B,T.C,T.A};
    for(int I=0;I<3;++I)
    {
        const FVector Edge=Verts[I+1]-Verts[I];
        double X=FVector::DotProduct(FVector::CrossProduct(Edge,O-Verts[I]),N);
        double V=FVector::DotProduct(FVector::CrossProduct(Edge,D),N);
        if(V==0){if(X<0)return false;continue;}
        double U=-X/V;if(V>0)A=FMath::Max(A,U);else B=FMath::Min(B,U);if(A>B)return false;
    }
    return true;
}
bool InsideClosedPolyhedron(FVector Point,TConstArrayView<FTriangle> Triangles)
{
    double Angle=0;
    for(const auto& T:Triangles)
    {
        if(SegmentTriangleClosed(Point,Point,T))return true;
        const FVector A=T.A-Point,B=T.B-Point,C=T.C-Point;
        const double LA=A.Size(),LB=B.Size(),LC=C.Size();
        Angle+=2*FMath::Atan2(FVector::DotProduct(A,FVector::CrossProduct(B,C)),
            LA*LB*LC+FVector::DotProduct(A,B)*LC+FVector::DotProduct(B,C)*LA+FVector::DotProduct(C,A)*LB);
    }
    return FMath::Abs(Angle)>2*UE_DOUBLE_PI;
}
TOptional<double> FirstVisible(FVector O0,FVector O1,FVector C0,FVector C1,double R,FContactRange Range,
    const TArray<FTriangle>& Triangles,TFunctionRef<bool(double)> Visible)
{
    if(!Range.bHit)return {};
    const FVector OV=O1-O0,D0=C0-O0,DV=(C1-C0)-OV;
    FPoly Len{D0.SizeSquared(),2*FVector::DotProduct(D0,DV),DV.SizeSquared()};
    TArray<double> Cuts{Range.Begin,Range.End};FPoly Near=Len;Near[0]-=R*R;Roots(Near,Range.Begin,Range.End,Cuts);
    FBox Swept(ForceInit);for(FVector P:{O0,O1,C0,C1})Swept+=P;Swept=Swept.ExpandBy(R);
    for(const auto& T:Triangles)
    {
        FBox Bounds(ForceInit);Bounds+=T.A;Bounds+=T.B;Bounds+=T.C;if(!Bounds.Intersect(Swept))continue;
        const FVector N=FVector::CrossProduct(T.B-T.A,T.C-T.A);
        const FPoly Den{FVector::DotProduct(N,D0),FVector::DotProduct(N,DV)};
        const FPoly Num{FVector::DotProduct(N,T.A-O0),-FVector::DotProduct(N,OV)};
        FPoly Rem{Den[0]-Num[0],Den[1]-Num[1]};
        Roots(Den,Range.Begin,Range.End,Cuts);Roots(Num,Range.Begin,Range.End,Cuts);Roots(Rem,Range.Begin,Range.End,Cuts);
        FPoly End=Mul(Mul(Rem,Rem),Len),Term=Mul(Den,Den);
        for(int I=0;I<Term.Num();++I)End[I]-=R*R*Term[I];Roots(End,Range.Begin,Range.End,Cuts);
        const FVector Verts[]={T.A,T.B,T.C,T.A};
        for(int I=0;I<3;++I)
        {
            FVector E=Verts[I+1]-Verts[I],A=Verts[I]-O0;
            FPoly Edge{FVector::DotProduct(FVector::CrossProduct(E,A),D0),
                FVector::DotProduct(FVector::CrossProduct(E,A),DV)-FVector::DotProduct(FVector::CrossProduct(E,OV),D0),
                -FVector::DotProduct(FVector::CrossProduct(E,OV),DV)};
            Roots(Edge,Range.Begin,Range.End,Cuts);
        }
    }
    Cuts.Sort();
    for(int I=0;I<Cuts.Num();++I)
    {
        double A=Cuts[I];if(Visible(A))return A;
        if(I+1==Cuts.Num()||Cuts[I+1]==A)continue;
        double B=A+(Cuts[I+1]-A)*.5;if(!Visible(B))continue;
        for(int K=0;K<96;++K){double M=A+(B-A)*.5;if(M==A||M==B)break;if(Visible(M))B=M;else A=M;}
        return B; // first representable validated visible point, never backdate to blocked boundary
    }
    return {};
}
void AddBoxTriangles(const FTransform& X,FVector H,TArray<FTriangle>& Out)
{
    FVector V[8];for(int I=0;I<8;++I)V[I]=X.TransformPosition(FVector(I&1?H.X:-H.X,I&2?H.Y:-H.Y,I&4?H.Z:-H.Z));
    const int Faces[][4]={{0,1,3,2},{4,6,7,5},{0,4,5,1},{2,3,7,6},{0,2,6,4},{1,5,7,3}};
    for(auto& F:Faces){Out.Add({V[F[0]],V[F[1]],V[F[2]]});Out.Add({V[F[0]],V[F[2]],V[F[3]]});}
}
}

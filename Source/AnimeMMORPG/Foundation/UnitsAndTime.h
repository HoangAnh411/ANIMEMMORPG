#pragma once

namespace AnimeMMORPG::Foundation
{
constexpr double MetersToCentimeters(double Meters) { return Meters * 100.0; }
constexpr double CentimetersToMeters(double Centimeters) { return Centimeters / 100.0; }
constexpr bool IsWithinHalfOpenInterval(double Now, double Start, double End)
{
    return Start < End && Now >= Start && Now < End;
}
}

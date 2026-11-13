#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#if PLATFORM_WINDOWS
#include "Windows/WindowsHWrapper.h"
#endif
namespace AnimeMMORPG::U01
{
// UE places ordinary letters in its character map, not necessarily its virtual-key map.
// Reconciliation must query the OS key corresponding to either mapping.
inline uint32 WindowsVirtualKey(FKey Key)
{
#if PLATFORM_WINDOWS
    const uint32 *KeyCode=nullptr,*CharCode=nullptr;uint32 Code=0;
    FInputKeyManager::Get().GetCodesFromKey(Key,KeyCode,CharCode);
    if(KeyCode)Code=*KeyCode;
    else if(CharCode && *CharCode<=0xffff)
    {const SHORT Mapped=::VkKeyScanW(WCHAR(*CharCode));if(Mapped!=-1)Code=uint32(Mapped)&0xff;}
    if(Key==EKeys::LeftMouseButton)Code=VK_LBUTTON;
    if(Key==EKeys::RightMouseButton)Code=VK_RBUTTON;
    if(Key==EKeys::MiddleMouseButton)Code=VK_MBUTTON;
    if(Key==EKeys::ThumbMouseButton)Code=VK_XBUTTON1;
    if(Key==EKeys::ThumbMouseButton2)Code=VK_XBUTTON2;
    return Code;
#else
    return 0;
#endif
}
}

import unreal
result=unreal.U02AnimationEditor.adjust_c_arm_mask()
unreal.log(result)
if not result.startswith('SUCCESS'):raise RuntimeError(result)

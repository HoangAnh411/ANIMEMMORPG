# Windows identity samples — Identity-Windows-03

Child Python ẩn, không game/Editor/HWND/input. FILETIME lưu số nguyên decimal100ns; không chuyển qua double khi đối chiếu.

|Sample|PID|FILETIME handle gốc|FILETIME query|CIM ticks|Delta ticks|Exited|
|---|---|---|---|---|---|---|
|1|18444|134397392087734855|134397392087734855|134397392087734850|5|True|
|2|2044|134397392097750293|134397392097750293|134397392097750290|3|True|
|3|19328|134397392107618930|134397392107618930|134397392107618930|0|True|
|4|1752|134397392117712083|134397392117712083|134397392117712080|3|True|
|5|20168|134397392127361907|134397392127361907|134397392127361900|7|True|

Recovery: status=INVALID, PID=15332, processExited=True, wait=signaled, handleSource=original_Popen. Metadata bị cố ý chặn; không có identity PASS, không vào probe, không pin được FILETIME.

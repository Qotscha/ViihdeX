'mpcPath = "C:\Program Files (x86)\MPC-HC\mpc-hc.exe"
mpcPath = "C:\Program Files\MPC-HC\mpc-hc64.exe"

Set objShell = CreateObject("Wscript.Shell")

newUrl = WScript.Arguments(0)
id = Left(newUrl, InStr(newUrl, "account=viihde") + 13)
id = Right(id, Len(id) - InStrRev(id, "/", InStrRev(id, "/") - 1))
' WScript.Echo id

For i = 0 to 49
	On Error Resume Next
	regValue = objShell.RegRead("HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Settings\File Name " & i)
	If InStr(regValue, id) Then
		objShell.RegWrite "HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Settings\File Name " & i, newUrl, "REG_SZ"
		objShell.RegWrite "HKEY_CURRENT_USER\Software\MPC-HC\MPC-HC\Recent File List\File" & i+1, newUrl, "REG_SZ"
		Exit For
	End If
Next

objShell.Run("""" & mpcPath & """ " & newUrl)
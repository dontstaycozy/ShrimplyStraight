Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

CurrentDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = CurrentDir

VenvPythonw = CurrentDir & "\venv\Scripts\pythonw.exe"

If FSO.FileExists(VenvPythonw) Then
    WshShell.Run """" & VenvPythonw & """ main.py", 0, False
Else
    WshShell.Run "pythonw main.py", 0, False
End If

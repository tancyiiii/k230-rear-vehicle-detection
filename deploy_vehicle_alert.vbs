Option Explicit
Dim shell, pc, canmv, sdcard, rear, src, item
Set shell = CreateObject("Shell.Application")
Set pc = shell.Namespace(17)
For Each item In pc.Items
  If item.Name = "CanMV" Then Set canmv = item
Next
If canmv Is Nothing Then
  WScript.Echo "CANMV_NOT_FOUND"
  WScript.Quit 1
End If
Set sdcard = canmv.GetFolder.ParseName("sdcard").GetFolder
Set rear = sdcard.ParseName("rear_vehicle").GetFolder
Set src = shell.Namespace("C:\Users\29813\AppData\Local\Temp\k230_audio")
Set item = rear.ParseName("rear_vehicle_yolo11.py")
If Not (item Is Nothing) Then
  item.Name = "rear_vehicle_yolo11_prev_no_thread_done.py"
  WScript.Sleep 1200
End If
rear.CopyHere src.ParseName("rear_vehicle_yolo11.py"), 16
WScript.Sleep 6000
WScript.Echo "DEPLOYED"

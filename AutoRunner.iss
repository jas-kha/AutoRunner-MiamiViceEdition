; -------------------------------
; AutoRunner Installer
; -------------------------------

#define MyAppName "AutoRunner"
#define MyAppVersion "1.0.0"
#define MyAppExeName "auto_runner.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-ABCDEF123456}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="JasKha"
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=AutoRunnerSetup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes

[Files]
Source:"dist\auto_runner.exe"; DestDir:"{app}"; Flags: ignoreversion
Source:"icon.ico"; DestDir:"{app}"

[Icons]
Name:"{group}\{#MyAppName}"; Filename:"{app}\{#MyAppExeName}"
Name:"{commondesktop}\AutoRunner"; Filename:"{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut";

[Run]
Filename:"{app}\{#MyAppExeName}"; Description:"Launch AutoRunner"; Flags: nowait postinstall

; -------------------------------
; AutoRunner Installer
; -------------------------------

#define MyAppName "Auto Runner"
#define MyAppVersion "0.2.2.0"
#define MyAppExeName "AutoRunner.exe"

[Setup]
AppId={{F3A9C5E2-7D4B-4C8F-9A6E-1B2D3C7F5A66}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="JK Software"
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=AutoRunnerSetup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes

[Files]
Source:"dist\AutoRunner.exe"; DestDir:"{app}"; Flags: ignoreversion
Source:"icon.ico"; DestDir:"{app}"

[Icons]
Name:"{group}\{#MyAppName}"; Filename:"{app}\{#MyAppExeName}"
Name:"{commondesktop}\AutoRunner"; Filename:"{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut";

[Run]
Filename:"{app}\{#MyAppExeName}"; Description:"Launch AutoRunner"; Flags: nowait postinstall

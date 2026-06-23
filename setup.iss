; Tmura - Inno Setup Script
; Creates Windows installer for Tmura Smart File Converter

#define MyAppName "Tmura"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tmura"
#define MyAppURL "https://github.com/tmura"
#define MyAppExeName "Tmura.exe"
#define ExtensionID "mefmiammilbcjogoclncpjcbpklgljal"

[Setup]
AppId={{8F3B7D9A-1234-5678-9ABC-DEF012345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=info_before.txt
OutputDir=installer_output
OutputBaseFilename=TmuraSetup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable
Source: "dist\Tmura.exe"; DestDir: "{app}"; Flags: ignoreversion

; Icon
Source: "dist\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; Extension folder
Source: "dist\extension\*"; DestDir: "{app}\extension"; Flags: ignoreversion recursesubdirs createallsubdirs

; App folder with host files
Source: "dist\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

; Requirements
Source: "dist\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Native Messaging Host registration - points to user-writable location in %APPDATA%
; This avoids permission crashes when the app (installed in Program Files) registers the host.
Root: HKCU; Subkey: "Software\Google\Chrome\NativeMessagingHosts\com.compressor.host"; ValueType: string; ValueName: ""; ValueData: "{code:GetManifestPath}"; Flags: uninsdeletevalue uninsdeletekeyifempty

[Code]
var
  PythonCheckPage: TOutputMsgWizardPage;

// Return the path to the user-writable native host manifest.
// Files are placed in %APPDATA%\Tmura\native_host\com.compressor.host.json
function GetManifestPath(Param: String): String;
begin
  Result := ExpandConstant('{userappdata}\Tmura\native_host\com.compressor.host.json');
end;

function InitializeSetup(): Boolean;
var
  PythonPath: String;
begin
  Result := True;

  // Check for Python installation
  PythonPath := '';
  if not RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
    if not RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
      if not RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
        if not RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
          // Python 3.10 fallback
          if not RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
            RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath);

  if PythonPath = '' then
    begin
      if MsgBox('Python 3.10+ is required but not found.' + #13#10 +
                'The app will still install, but native messaging will not work.' + #13#10 + #13#10 +
                'Please install Python from python.org and reinstall.' + #13#10 + #13#10 +
                'Continue anyway?', mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  PythonExe: String;
  WrapperPath: String;
  HostPyPath: String;
  HostDir: String;
  ManifestPath: String;
  ManifestContent: String;
  F: Text;
begin
  if CurStep = ssPostInstall then
    begin
      // Find system Python (prefer python.exe on PATH)
      PythonExe := ExpandConstant('{cmd}');
      if PythonExe = '' then
        PythonExe := 'python';

      // Write the wrapper and manifest to a user-writable location
      // (%APPDATA%\Tmura\native_host), not to Program Files.
      HostDir := ExpandConstant('{userappdata}\Tmura\native_host');
      if not DirExists(HostDir) then
        CreateDir(HostDir);

      WrapperPath := HostDir + '\host_wrapper.bat';
      HostPyPath := ExpandConstant('{app}\app\host.py');

      AssignFile(F, WrapperPath);
      Rewrite(F);
      WriteLn(F, '@echo off');
      WriteLn(F, '"' + PythonExe + '" "' + HostPyPath + '" %*');
      CloseFile(F);

      ManifestPath := HostDir + '\com.compressor.host.json';
      ManifestContent := '{' + #13#10 +
        '  "name": "com.compressor.host",' + #13#10 +
        '  "description": "Tmura Native Host",' + #13#10 +
        '  "path": "' + WrapperPath + '",' + #13#10 +
        '  "type": "stdio",' + #13#10 +
        '  "allowed_origins": [' + #13#10 +
        '    "chrome-extension://{#ExtensionID}/"' + #13#10 +
        '  ]' + #13#10 +
        '}';

      AssignFile(F, ManifestPath);
      Rewrite(F);
      Write(F, ManifestContent);
      CloseFile(F);
    end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  HostDir: String;
begin
  if CurUninstallStep = usPostUninstall then
    begin
      // Remove native messaging host registration
      RegDeleteKeyIncludingSubkeys(HKCU, 'Software\Google\Chrome\NativeMessagingHosts\com.compressor.host');

      // Optionally remove the user-writable native_host directory
      HostDir := ExpandConstant('{userappdata}\Tmura\native_host');
      if DirExists(HostDir) then
        DelTree(HostDir, True, True, True);
    end;
end;

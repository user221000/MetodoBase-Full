; Script de Inno Setup para crear instalador profesional de Método Base
; Requiere Inno Setup 6.x: https://jrsoftware.org/isinfo.php
;
; Uso:
;   1. Instala Inno Setup
;   2. Abre este archivo en Inno Setup Compiler
;   3. Compila (Ctrl+F9)
;   4. Se genera: Output\MetodoBaseSetup_v1.0.0.exe

#define MyAppName "Método Base"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "MetodoBase"
#define MyAppURL "https://metodobase.com"
#define MyAppExeName "MetodoBase.exe"

[Setup]
AppId={{8A2F4E7B-3C9D-4B1A-A5E6-7F8D9C0B2E3A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

OutputDir=Output
OutputBaseFilename=MetodoBaseSetup_v{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes

PrivilegesRequired=admin

WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MetodoBase\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\registros"
Type: filesandordirs; Name: "{app}\planes"
Type: filesandordirs; Name: "{app}\logs"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpWelcome then
  begin
    WizardForm.WelcomeLabel2.Caption :=
      'Este asistente te guiará en la instalación de ' +
      '{#MyAppName} v{#MyAppVersion}.' + #13#10#13#10 +
      'Sistema profesional de generación de planes nutricionales ' +
      'para gimnasios.' + #13#10#13#10 +
      'Desarrollado por {#MyAppPublisher}';
  end;
end;

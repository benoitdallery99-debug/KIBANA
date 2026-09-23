# outils/diagnostic-windows.ps1 — ce que le poste Windows permet, AVANT d'installer.
#
# Lecture seule : ce script ne modifie rien, n'installe rien, n'exige aucun
# droit d'administration. Il relève ce qui décide de la faisabilité du lab
# (docs/INSTALLATION_WINDOWS.md, §1 et §2) et écrit un rapport à recopier.
# Il n'affiche ni le nom du poste, ni celui de l'utilisateur, ni aucun secret.
#
# Compatible Windows PowerShell 5.1 (celui livré avec Windows) :
#   powershell -ExecutionPolicy Bypass -File .\diagnostic-windows.ps1

$ErrorActionPreference = 'Continue'
$env:WSL_UTF8 = '1'   # wsl.exe écrit sinon en UTF-16, illisible une fois capturé
$lignes = New-Object System.Collections.Generic.List[string]
$bloquants = 0

function Note([string]$etat, [string]$texte) {
    $ligne = '[{0}] {1}' -f $etat, $texte
    $script:lignes.Add($ligne)
    $couleur = switch ($etat) { 'OK' { 'Green' } '!!' { 'Red' } default { 'Yellow' } }
    Write-Host $ligne -ForegroundColor $couleur
    if ($etat -eq '!!') { $script:bloquants++ }
}
function Titre([string]$texte) {
    $script:lignes.Add('')
    $script:lignes.Add("== $texte ==")
    Write-Host ''
    Write-Host "== $texte ==" -ForegroundColor Cyan
}
function Nettoyer([string]$s) { return ($s -replace "`0", '').Trim() }

Titre 'Systeme'
$os = Get-CimInstance Win32_OperatingSystem
$build = [int]$os.BuildNumber
if ($build -ge 19041) {
    Note 'OK' ("{0}, build {1} (WSL2 exige 19041 ou plus)" -f $os.Caption, $build)
} else {
    Note '!!' ("{0}, build {1} : WSL2 exige la build 19041 (Windows 10 2004) ou plus" -f $os.Caption, $build)
}

$arch = $env:PROCESSOR_ARCHITECTURE
if ($env:PROCESSOR_ARCHITEW6432) { $arch = $env:PROCESSOR_ARCHITEW6432 }
if ($arch -eq 'AMD64') {
    Note 'OK' 'processeur x86_64 : les images du lab (linux/amd64) peuvent tourner'
} else {
    Note '!!' ("processeur {0} : les images du lab sont linux/amd64 et ne demarreront pas" -f $arch)
}

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if ($admin) { Note 'OK' 'session administrateur' }
else { Note '--' 'session NON administrateur : certains controles ci-dessous seront partiels' }

Titre 'Ressources'
$ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
if ($ram -ge 16) { Note 'OK' ("{0} Go de RAM (16 recommandes, le lab en exige 6 dans WSL2)" -f $ram) }
elseif ($ram -ge 8) { Note '--' ("{0} Go de RAM : le lab tournera, la suite de verification complete non" -f $ram) }
else { Note '!!' ("{0} Go de RAM : insuffisant, le lab exige 6 Go dans WSL2 en plus de Windows" -f $ram) }

$c = Get-PSDrive -Name C -ErrorAction SilentlyContinue
if ($c) {
    $libre = [math]::Round($c.Free / 1GB, 1)
    if ($libre -ge 15) { Note 'OK' ("{0} Go libres sur C: (15 recommandes)" -f $libre) }
    else { Note '!!' ("{0} Go libres sur C: : il en faut 15 (distribution, images, index)" -f $libre) }
}

Titre 'Virtualisation'
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$hyperviseur = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
# Piège connu : quand un hyperviseur tourne déjà, VirtualizationFirmwareEnabled
# répond False alors que la virtualisation est bel et bien active.
if ($hyperviseur) {
    Note 'OK' 'un hyperviseur tourne deja : la virtualisation materielle est active'
} elseif ($cpu.VirtualizationFirmwareEnabled) {
    Note 'OK' 'virtualisation materielle active dans le firmware'
} else {
    Note '!!' 'virtualisation materielle INACTIVE : a activer dans le BIOS/UEFI (Intel VT-x ou AMD-V)'
}

Titre 'WSL'
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Note '!!' 'wsl.exe absent : WSL n''est pas installe'
} else {
    $version = Nettoyer ((& wsl.exe --version 2>&1) | Out-String)
    if ($LASTEXITCODE -eq 0 -and $version -match 'WSL') {
        $premiere = ($version -split "`n")[0].Trim()
        Note 'OK' ("WSL installe : {0}" -f $premiere)
    } else {
        Note '--' 'wsl.exe present mais « wsl --version » ne repond pas : WSL ancien ou pas encore installe'
    }
    $liste = Nettoyer ((& wsl.exe -l -v 2>&1) | Out-String)
    if ($LASTEXITCODE -eq 0 -and $liste) {
        Note 'OK' 'distributions installees :'
        foreach ($l in ($liste -split "`n")) { if ($l.Trim()) { $lignes.Add('       ' + $l.TrimEnd()); Write-Host ('       ' + $l.TrimEnd()) } }
    } else {
        Note '--' 'aucune distribution WSL installee'
    }
}

if ($admin) {
    foreach ($f in 'Microsoft-Windows-Subsystem-Linux', 'VirtualMachinePlatform') {
        $etat = (Get-WindowsOptionalFeature -Online -FeatureName $f -ErrorAction SilentlyContinue).State
        if ($etat -eq 'Enabled') { Note 'OK' "fonctionnalite $f activee" }
        else { Note '--' "fonctionnalite $f : $etat (wsl --install l'active)" }
    }
} else {
    Note '--' 'fonctionnalites Windows non verifiables sans droits administrateur'
}

$politique = @('HKLM:\SOFTWARE\Policies\Microsoft\Windows\WSL', 'HKLM:\SOFTWARE\Policies\WSL') |
    Where-Object { Test-Path $_ }
if ($politique) { Note '!!' ("strategie de groupe WSL presente ({0}) : a faire examiner par la DSI" -f ($politique -join ', ')) }
else { Note 'OK' 'aucune strategie de groupe WSL detectee' }

$wslconfig = Join-Path $env:USERPROFILE '.wslconfig'
if (Test-Path $wslconfig) {
    Note '--' '.wslconfig existe deja :'
    foreach ($l in Get-Content $wslconfig) { $lignes.Add('       ' + $l); Write-Host ('       ' + $l) }
} else {
    Note '--' '.wslconfig absent (il faudra le creer, voir INSTALLATION_WINDOWS.md §4.3)'
}

Titre 'Ports et logiciels deja presents'
foreach ($port in 9200, 5601) {
    $pris = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($pris) {
        $proc = (Get-Process -Id ($pris | Select-Object -First 1).OwningProcess -ErrorAction SilentlyContinue).ProcessName
        Note '!!' ("port {0} deja occupe par « {1} » : KIT_PORT_ES / KIT_PORT_KIBANA permettent d'en changer" -f $port, $proc)
    } else {
        Note 'OK' "port $port libre"
    }
}
foreach ($outil in 'podman', 'docker', 'git') {
    $o = Get-Command "$outil.exe" -ErrorAction SilentlyContinue
    if ($o) { Note '--' ("{0} present cote Windows : {1}" -f $outil, $o.Source) }
    else { Note '--' "$outil absent cote Windows (normal : tout se passera dans WSL2)" }
}
$av = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction SilentlyContinue
if ($av) { Note '--' ("antivirus : {0} (prevoir une exclusion sur le disque de la distribution WSL)" -f (($av | ForEach-Object displayName) -join ', ')) }

Titre 'Reseau'
foreach ($hote in 'https://github.com', 'https://mirror.gcr.io/v2/', 'https://pypi.org/simple/') {
    try {
        $null = Invoke-WebRequest -Uri $hote -Method Head -UseBasicParsing -TimeoutSec 8 -ErrorAction Stop
        Note 'OK' "$hote joignable"
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        # 401 ou 405 veulent dire que le serveur a répondu : le réseau passe.
        if ($code -in 401, 403, 405) { Note 'OK' "$hote joignable (HTTP $code)" }
        else { Note '--' "$hote injoignable : l'installation se fera hors ligne" }
    }
}

Titre 'Synthese'
if ($bloquants -eq 0) { Note 'OK' 'aucun blocage : le poste peut accueillir le lab dans WSL2' }
else { Note '!!' ("{0} blocage(s) a lever avant toute installation" -f $bloquants) }

$bureau = [Environment]::GetFolderPath('Desktop')
$rapport = Join-Path $bureau 'diagnostic-kit-kibana.txt'
$lignes | Set-Content -Path $rapport -Encoding UTF8
Write-Host ''
Write-Host "Rapport ecrit dans : $rapport" -ForegroundColor Cyan
Write-Host 'Copiez son contenu dans la conversation.' -ForegroundColor Cyan

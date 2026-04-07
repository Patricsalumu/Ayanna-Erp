<#
Crée des raccourcis Desktop et Start Menu pour l'application, et tente d'épingler
l'application à la barre des tâches.

Usage :
  # Exécution simple (depuis la racine du projet)
  .\scripts\create_shortcuts.ps1 -ExePath ".\\dist\\AyannaErp\\AyannaErp.exe" -IconPath ".\\data\\images\\icone_ayanna_erp.ico" -PinTaskbar

Paramètres :
  -ExePath   : chemin vers l'exécutable
  -IconPath  : chemin vers le fichier .ico
  -PinTaskbar: si présent, tente d'épingler à la barre des tâches

Notes :
- L'opération d'épinglage peut échouer selon la version/paramètres de Windows et
  les politiques de sécurité. Le script essaie plusieurs verbes localisés.
- Pour que l'épinglage fonctionne, il est souvent nécessaire que le raccourci
  soit dans un emplacement utilisateur (Start Menu / Desktop).
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ExePath = ".\dist\AyannaErp\AyannaErp.exe",

    [Parameter(Mandatory=$false)]
    [string]$IconPath = ".\data\images\icone_ayanna_erp.ico",

    [Parameter(Mandatory=$false)]
    [switch]$PinTaskbar
)

function Resolve-FullPath([string]$p) {
    try {
        return (Resolve-Path -Path $p -ErrorAction Stop).Path
    } catch {
        return $null
    }
}

$exeFull = Resolve-FullPath $ExePath
if (-not $exeFull) {
    Write-Error "Executable introuvable: $ExePath"
    exit 1
}

$iconFull = Resolve-FullPath $IconPath
if (-not $iconFull) {
    Write-Warning "Icône introuvable: $IconPath. Le raccourci utilisera l'icône par défaut."
}

$shell = New-Object -ComObject WScript.Shell

# --- Création du raccourci Bureau ---
$desktopFolder = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
$desktopLnk = Join-Path $desktopFolder 'Ayanna ERP.lnk'
try {
    $lnk = $shell.CreateShortcut($desktopLnk)
    $lnk.TargetPath = $exeFull
    $lnk.WorkingDirectory = Split-Path $exeFull
    if ($iconFull) { $lnk.IconLocation = "$iconFull,0" }
    $lnk.Save()
    Write-Host "Raccourci Bureau créé : $desktopLnk"
} catch {
    Write-Warning "Impossible de créer le raccourci Bureau : $_"
}

# --- Création du raccourci Menu Démarrer (Programs) ---
$programsFolder = [Environment]::GetFolderPath([Environment+SpecialFolder]::Programs)
$startLnk = Join-Path $programsFolder 'Ayanna ERP.lnk'
try {
    $lnk2 = $shell.CreateShortcut($startLnk)
    $lnk2.TargetPath = $exeFull
    $lnk2.WorkingDirectory = Split-Path $exeFull
    if ($iconFull) { $lnk2.IconLocation = "$iconFull,0" }
    $lnk2.Save()
    Write-Host "Raccourci Menu Démarrer créé : $startLnk"
} catch {
    Write-Warning "Impossible de créer le raccourci Menu Démarrer : $_"
}

# --- Tenter d'épingler à la barre des tâches ---
if ($PinTaskbar) {
    try {
        $shellApp = New-Object -ComObject Shell.Application
        $lnkPath = $desktopLnk
        if (-not (Test-Path $lnkPath)) { $lnkPath = $startLnk }
        if (-not (Test-Path $lnkPath)) { throw "Aucun raccourci trouvé pour l'épinglage." }

        $folder = Split-Path $lnkPath
        $fileName = Split-Path $lnkPath -Leaf
        $folderItem = $shellApp.Namespace($folder).ParseName($fileName)
        if (-not $folderItem) { throw "Impossible d'obtenir FolderItem pour $lnkPath" }

        $verbs = @()
        $folderItem.Verbs() | ForEach-Object { $verbs += $_.Name }

        # Verbs possibles (anglais/français) — la chaîne exacte dépend de la langue Windows
        $want = @(
            'Pin to taskbar',
            'Pin to Tas&kbar',
            'Épingler à la barre des tâches',
            'Épingler à la barre des tâches(&T)'
        )

        $found = $false
        $i = 0
        $folderItem.Verbs() | ForEach-Object {
            $name = $_.Name
            foreach ($w in $want) {
                if ($name -like "*$w*") {
                    Write-Host "Exec verb: $name"
                    $_.DoIt()
                    $found = $true
                    break
                }
            }
            if ($found) { return }
            $i++
        }

        if (-not $found) {
            Write-Warning "Verbe d'épinglage non trouvé automatiquement. Vous pouvez épingler manuellement depuis le raccourci créé sur le Bureau."
        } else {
            Write-Host "Tâche d'épinglage effectuée. Vérifiez la barre des tâches."
        }
    } catch {
        Write-Warning "Échec de l'épinglage automatique : $_. Exception"
        Write-Host "Essayez d'épingler manuellement le raccourci créé sur le Bureau."
    }
}

Write-Host 'Opération terminée.'

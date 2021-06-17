# LICENSE: AGPLv3. See LICENSE at root of repo

$targets = get-AppxPackage
$targets = $targets.where{ -not $_.IsFramework }

$apps = @()
foreach ($app in $targets)
{
    try
    {
        $app_manifest = Get-AppxPackageManifest $app;
        $id = $app_manifest.package.applications.application.id;
        # Older games (like Prey) are App.
        if ($id -eq 'Game' -or $id -eq 'App')
        {
            $name = $app_manifest.Package.Properties.DisplayName;
            if ($name -like '*DisplayName*' -or $name -like '*ms-resource*')
            {
                # Invalid name is probably not a game.
                continue;
            }

            # Small icon looks better in steam. The Square150x150Logo is better for a desktop shortcut.
            $icon = $app.InstallLocation + "\" + $app_manifest.Package.Applications.Application.VisualElements.Square44x44Logo;
            $apps += [pscustomobject]@{
                Kind = $id
                Appid = $app.Name
                PrettyName = $name
                Icon = $icon
                InstallLocation = $app.InstallLocation
                #~ Aumid = $app.PackageFamilyName + "!" + $id
            };
        }
    }
    catch
    {
    }
}

$apps | ConvertTo-Json -depth 100;

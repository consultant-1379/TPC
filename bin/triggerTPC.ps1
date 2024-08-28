# *************************************************************************
# 	Ericsson Radio Systems AB                                     SCRIPT
# *************************************************************************
# 
#   (c) Ericsson Radio Systems AB 2018 - All rights reserved.
#   The copyright to the computer program(s) herein is the property
# 	and/or copied only with the written permission from Ericsson Radio
# 	Systems AB or in accordance with the terms and conditions stipulated
# 	in the agreement/contract under which the program(s) have been
# 	supplied.
#
# *************************************************************************
# 	Name    : triggerTPC.ps1
# 	Date    : 21/10/2018
# 	Revision: R1A20
# 	Purpose : Wrapper script to trigger TPC to make it easy to use [Menu driven]
#
# 	Usage   : triggerTPC.ps1 -modelt <full path to Model-T>
# *************************************************************************

# Check arguments
param(
	[Parameter(Mandatory=$true)][string]$ModelT
)

# Set values
$Options = @("Create TP Only", "Create TP And Create Universe", "Create TP And Update Universe", "Create Universe Only", "Update Universe Only", "Create Universe Reference Document", "Find Delta", "Create BO Package Only", "Exit")
$EnvDirPath = "$pwd" + "\EnvDeploy"
$CommonFilePath = $EnvDirPath + "\commonFiles.zip"
if(-not (Test-Path $CommonFilePath)){
	Write-Host "Common Environment files not present in $EnvDirPath!"
	Write-Host "Copy commonFiles.zip file to $EnvDirPath and try again."
	exit
}
$TempOutFolder = "$pwd" + "\TempOutFolder"
$OutputFolder = "$pwd" +  "\TPIOutput"
$UniOutputFolder = "$pwd" +  "\UnvOutput"
$UniInputFolder = "$pwd" +  "\unvDetails"

Function triggerTPC{
	java -cp libs/* com.ericsson.eniq.tpc.TPC "$args"
}

Function FetchEniqEnv{
	$EnvPropsFile = "$pwd" + "\CollectEnvProperties"
	"--Collect Environment" | Out-File -FilePath $EnvPropsFile -Encoding ASCII
	"ModuleName::TPC.PackageEnv" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	$ServerName = Read-Host -Prompt 'Enter ENIQ server address'
	$UserName = Read-Host -Prompt 'Enter ENIQ server Username'
	$Password = Read-Host -Prompt 'Enter ENIQ server Password'
	$Port = Read-Host -Prompt 'Enter ENIQ server SSH Port'
	"Servername::$ServerName" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	"Username::$UserName" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	"Password::$Password" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	"OutputPath::$EnvDirPath" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	"Port::$Port" | Out-File -FilePath $EnvPropsFile -Encoding ASCII -Append
	triggerTPC $EnvPropsFile
}

Function PushTP{
	$TpiFile = "$TempOutFolder" + "\" + "$args"
	$PushTPFile = "$pwd" + "\PushTPProps_$args"
	$PushTPFile = $PushTPFile.replace("_TEST.xlsx","")
	"--Create TP" | Out-File -FilePath $PushTPFile -Encoding ASCII
	"ModuleName::TPC.PushTP" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"SourceType::XLSX" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"TpceFile::$EnvFilePath" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"TpceCommonFiles::$CommonFilePath" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"InputFilePath::$TpiFile" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"DeployPath::$EnvDirPath" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	"tpiOutputPath::$OutputFolder" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	if("$args".StartsWith("INTF")){
		"ModelType::INTF" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
	}
	else{
		"ModelType::TP" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
		if($Task -ne "Create TP Only"){
			"UniOutputPath::$UniOutputFolder" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			"UniInputPath::$UniInputFolder" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			"UniverseConnection::$UniConn" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			if($Task -eq "Create TP And Update Universe"){
				"UniverseTask::updateUnvOffline" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			}
			else{
				"UniverseTask::createUnvOffline" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			}
			if($rState -ne ""){
				"rState::$rState" | Out-File -FilePath $PushTPFile -Encoding ASCII -Append
			}
		}
	}
	triggerTPC $PushTPFile
	Move-Item -Path $PushTPFile -Destination $TempOutFolder
}

Function PushUnv{
	$TpiFile = "$TempOutFolder" + "\" + "$args"
	$PushUnvFile = "$pwd" + "\PushUnvProps_$args"
	$PushUnvFile = $PushUnvFile.replace("_TEST.xlsx","")
	"--Create Unv" | Out-File -FilePath $PushUnvFile -Encoding ASCII
	"ModuleName::TPC.PushUnv" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"SourceType::XLSX" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"TpceFile::$EnvFilePath" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"TpceCommonFiles::$CommonFilePath" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"InputFilePath::$TpiFile" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"DeployPath::$EnvDirPath" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"UniOutputPath::$UniOutputFolder" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"UniInputPath::$UniInputFolder" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"UniverseConnection::$UniConn" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	"ModelType::TP" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	if($Task -eq "Update Universe Only"){
		"UniverseTask::updateUnvOffline" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	}
	else{
		"UniverseTask::createUnvOffline" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	}
	if($rState -ne ""){
		"rState::$rState" | Out-File -FilePath $PushUnvFile -Encoding ASCII -Append
	}
	triggerTPC $PushUnvFile
	Move-Item -Path $PushUnvFile -Destination $TempOutFolder
}

Function PushUnvDoc{
	$TpiFile = "$TempOutFolder" + "\" + "$args"
	$PushDocFile = "$pwd" + "\PushDocProps_$args"
	$PushDocFile = $PushDocFile.replace("_TEST.xlsx","")
	"--Create Universe Ref Document" | Out-File -FilePath $PushDocFile -Encoding ASCII
	"ModuleName::TPC.PushUnvDoc" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"TpceFile::$EnvFilePath" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"TpceCommonFiles::$CommonFilePath" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"InputFilePath::$TpiFile" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"DeployPath::$EnvDirPath" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"SourceType::XLSX" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"UniOutputPath::$UniOutputFolder" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	"ModelType::TP" | Out-File -FilePath $PushDocFile -Encoding ASCII -Append
	triggerTPC $PushDocFile
	Move-Item -Path $PushDocFile -Destination $TempOutFolder
}

############################################ MAIN ##########################################

# Check if Model-T exists
if((-not (Test-Path $ModelT)) -or (-not ([IO.Path]::GetExtension($ModelT) -eq ".xlsx"))){
	Write-Host "`n`Model-T DOES NOT EXIST or NOT OF .XLSX TYPE`n"
	exit
}

# Choose task to perform
Write-Host "`n`t`t`** CHOOSE TASK TO PERFORM **"
Write-Host "`n`OPTIONS :"
for($opt=1; $opt -le $Options.Count ; $opt++){
	$Option = $Options[$opt - 1]
	Write-Host "[$opt] $Option"
}
while($true){
	$Entry = Read-Host -Prompt "`n`Enter serial number of task to be performed"
	$Entry = [int]($Entry.trim())
	if(($Entry -match "^[\d\.]+$") -and ($Entry -gt 0) -and ($Entry -le $Options.Count)){
		$Task = $Options[$Entry - 1]
		break
	}
	else{
		Write-Host "`n`Incorrect choice!"
	}
}

if($Task -eq "Exit"){
	Write-Host "`n`EXITING TPC`n"
	exit
}

#TPC delta Feature
if($Task -eq "Find Delta"){
	Write-Host "`n`------------TPC DELTA FEATURE-----------`n"
	triggerTPC "findDelta"
	exit
}

#Creating BO Package
if($Task -eq "Create BO Package Only"){
	Write-Host "`n`t`t`** CREATING BO PACKAGE **"
	$currentDir = "$pwd"
	$InputFile = [string]$ModelT
    $InputFile = $InputFile.replace(".\","")    
    $File_name = $InputFile.Split(".")
    $BO_package_name = $File_name[0]
    $BOFile = $BO_package_name.Split("_")
    $len = $BOFile.length-3
	$BOFile = $BOFile[1..$len]
    $Techpackname = "BO"
    foreach ($element in $BOFile)
    {
    $Techpackname += "_" + $element
    }
	$files = Get-ChildItem -Path "$UniOutputFolder"
	foreach ($item in $files) {
		if ($item.Attributes -eq "Directory") {
			if (($item.name).Contains($BOFile[2]) -AND ($item.name).Contains($BOFile[3])) {
				$DCPackagePath = $UniOutputFolder + "\$item"
				$UnvPath = $DCPackagePath + "\unv"
				$InstallPath = $DCPackagePath + "\install"
				if((Test-Path ("$InstallPath" + "\version.properties")) -and (Test-Path ("$UnvPath" + "\*.lcmbiar"))){	
					$BOzipPackage = $DCPackagePath + "\BO_package.zip"  
					$file = Get-ChildItem -Path "$UnvPath"
					$lcmbiarfile = $file.name.Split(".");
					$BO=$lcmbiarfile.Split("_");
					$BO_release_version = $Techpackname + "_" + $BO[1] + "_" + $BO[2] + ".tpi"
					$7zipPath = "C:\Program Files\7-Zip\7z.exe"		
					if (-not (Test-Path -Path $7zipPath -PathType Leaf)) {	
						Write-Host "7 zip file '$7zipPath' not found"
						exit
					}
					cd $DCPackagePath
					&"$7zipPath" a "$BOzipPackage" ".\unv", ".\install"
					cd $currentDir
					Rename-Item -LiteralPath $BOzipPackage -NewName $BO_release_version
					$BOtpiPackage = $DCPackagePath + "\$BO_release_version"
					powershell -ExecutionPolicy ByPass -File .\encryptDecrypt.ps1 -encrypt $BOtpiPackage
					Write-Host "`n`**SUCCESSFULLY CREATED BO PACKAGE** "
					Write-Host "`n`Encrypted file saved to : $BOtpiPackage  "	
					exit
				}	
				else{
				Write-Host "`n`lcmbiar file or version.properties files are not present in $item Directory. `n"
				exit
				}
			}	
		}
	}
	Write-Host "BO PACKAGE CREATION FAILED `n"
	Write-Host "Check below Conditions: - "
	Write-Host "1) UnvOutput Folder should not be empty. "
	Write-Host "2) It should contain Directory in the format DC_E_<TP Name>_((<Build Number>)) "
	Write-Host "   where the TP Name and Build Number should be same as defined in MODEL-T Name.`n "	
	exit
}

if(-not(($Task -eq "Create TP Only") -or ($Task -eq "Create Universe Reference Document"))){
	$UniConn = ""
	while ($UniConn -eq ""){
		$UniConn = Read-Host -Prompt "`n`Please provide the name of a Universe Connection present in the server"
	}
	
}

# Check ENIQ level
Write-Host "`n`t`t`** ENIQ ENVIRONMENT CHECK **"
if(Test-Path ("$EnvDirPath" + "\TPC_ENIQ-*.zip")){
	$CurrEniqLevel = [string](Get-ChildItem -Path $EnvDirPath -Filter "*TPC_ENIQ-*.zip")
	$CurrEniqLevel = $CurrEniqLevel.Replace("TPC_ENIQ-","")
	$CurrEniqLevel = $CurrEniqLevel.Replace(".zip","")
	while($true){
		# Check if new ENIQ level required
		$NewEnv = Read-Host -Prompt "`n`Continue with current ENIQ Design Environment - $CurrEniqLevel ? Y or N"
		if($NewEnv -eq "Y"){
			Write-Host "`n`ENIQ Design Environment is $CurrEniqLevel"
			break
		}
		elseif($NewEnv -eq "N"){
			# Start Collect env
			Remove-Item -Path ("$EnvDirPath" + "\TPC_ENIQ-*.zip")
			FetchEniqEnv
			break
		}
	}
}
else{
	FetchEniqEnv
}
$EnvFilePath = $EnvDirPath + "\" + (Get-ChildItem -Path $EnvDirPath -Filter "*TPC_ENIQ-*.zip")

# Convert to individual xlsx
Write-Host "`n`t`t`** MODEL-T CONVERSION START **"
$ConvertProps = "$pwd" + "\ConvertModel"
if(Test-Path $TempOutFolder){
	Remove-Item -Path $TempOutFolder -recurse
}
New-Item -ItemType directory -Path $TempOutFolder | Out-Null
"--Convert Model" | Out-File -FilePath $ConvertProps -Encoding ASCII
"ModuleName::TPC.convert" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
"ModelType::TP" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
"SourceType::LEGACY_XLSX" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
"InputFilePath::$ModelT" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
"WriteType::XLSX" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
"OutputPath::$TempOutFolder" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
triggerTPC $ConvertProps

# Check if conversion was successful
$ListOfTpis = ([string](Get-ChildItem -Path $TempOutFolder -Exclude *.txt -Name)).split(" ")
$tpiCount = $ListOfTpis.Count
if($tpiCount -eq 0) {
	exit
}
if(($Task -eq "Create TP Only") -or ($Task -eq "Create TP And Create Universe") -or ($Task -eq "Create TP And Update Universe")){
	# Choose what needs to be created using CLI menu
	Write-Host "`n`t`t`** TECHPACK CREATION CHECK **"
	Write-Host "`n`AVAILABLE TECHPACKS :"
	for($i=1; $i -le $ListOfTpis.Count ; $i++){
		$Tpi = $ListOfTpis[$i -1].Replace("_TEST.xlsx","")
		Write-Host "[$i] $Tpi"
	}

	while($true){
		$err = 0
		$ToCreate = @()
		$Choice = Read-Host -Prompt "`n`Enter serial number of TP you wish to create from the list given above. For multiple entries, please separate the choices using comma (,)"
		$Choice = $Choice.split(",")
		foreach($ind in $Choice){
			$ind = [int]($ind.trim())
			if(($ind -match "^[\d\.]+$") -and ($ind -gt 0) -and ($ind -le $tpiCount)){
				$ToCreate += $ListOfTpis[$ind - 1]
			}
			else{
				$err++
			}
		}
		if($err -eq 0){
			break
		}
		Write-Host "`n`Incorrect choice!"
	}
	$ToCreate = $ToCreate | select -uniq

	# Start TP creation
	if(-not (Test-Path $OutputFolder)){
		New-Item -ItemType directory -Path $OutputFolder | Out-Null
	}

	foreach($Package in $ToCreate){
		PushTP $Package
	}
}
else{
	Write-Host "`n`t`t`** UNIVERSE TASK START **"
	$ToCreateUnv = @()
	foreach($tp  in $ListOfTpis){
		if(-not ($tp.StartsWith("INTF"))){
			$ToCreateUnv += $tp
		}
	}
	if($ToCreateUnv.Count -eq 1){
		if($Task -eq "Create Universe Reference Document"){
			PushUnvDoc $ToCreateUnv[0]
		}
		else{
			PushUnv $ToCreateUnv[0]
		}
	}
	elseif($ToCreateUnv.Count -gt 1){
		Write-Host "`n`Multiple TPs created - please check`n"
		exit
	}
	else{
		Write-Host "`n`No TPs created - please check`n"
		exit
	}
}
Move-Item -Path $ConvertProps -Destination $TempOutFolder


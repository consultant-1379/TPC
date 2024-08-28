# *************************************************************************
# 	Ericsson Radio Systems AB                                     SCRIPT
# *************************************************************************
# 
#   (c) Ericsson Radio Systems AB 2019 - All rights reserved.
#   The copyright to the computer program(s) herein is the property
# 	and/or copied only with the written permission from Ericsson Radio
# 	Systems AB or in accordance with the terms and conditions stipulated
# 	in the agreement/contract under which the program(s) have been
# 	supplied.
#
# *************************************************************************
# 	Name    : debugTPC.ps1
# 	Date    : 21/05/2019
# 	Revision: R1A29
# 	Purpose : Wrapper script for using the debug features in TPC [Menu driven]
#
# 	Usage   : debugTPC.ps1 -[makeXls|convertVector] <full path to package>
# *************************************************************************

# Check arguments
param(
	[string]$makeXls = "",
	[string]$convertVector = ""
)

Function usage{
	Write-Host "`n`Usage:"
	Write-Host "debugTPC.ps1 -[makeXls|convertVector] <full path to package>`n"
}

Function debugTPC{
	java -cp libs/* com.ericsson.eniq.tpc.TPC "$args"
}

# Check if debug action was successful
Function chkSuccess{
	$ListOfTps = ([string](Get-ChildItem -Path $OutputFolder -Name)).split(" ")
	$tpCount = $ListOfTps.Count
	if($tpCount -eq 0) {
		Write-Host "`n`Conversion was not successful`n"
		Move-Item -Path $ConvertProps -Destination $OutputFolder
		exit
	}
	else{
		Write-Host "`n`Conversion was successful`n"
		Remove-Item -Path $ConvertProps
		exit
	}
}

# Convert to individual xlsx
Function convertTP{
	# Check if Techpack installer file exists
	if((-not (Test-Path $makeXls)) -or (-not ([IO.Path]::GetExtension($makeXls) -eq ".tpi"))){
		Write-Host "`n`Techpack installer NOT IN CORRECT .TPI Format`n"
		exit
	}

	$makeXls = $makeXls.Substring($makeXls.LastIndexOf("\") + 1)

	$OutputFolder = $DebugFolder + "\$makeXls"
	$OutputFolder = $OutputFolder.replace(".tpi","") + "_MODELT"
	$InputFilePath = "$pwd" + "\$makeXls"
	
	if(Test-Path $OutputFolder){
		Remove-Item -Path $OutputFolder -recurse
	}
	New-Item -ItemType directory -Path $OutputFolder | Out-Null
	Write-Host "`n`t`t`** TECHPACK CONVERSION START **"
	"--Make XLSX Model" | Out-File -FilePath $ConvertProps -Encoding ASCII
	"ModuleName::Debug.MakeXlsx" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	if($makeXls.StartsWith("INTF")){
		"ModelType::INTF" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	}
	else{
		"ModelType::TP" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	}
	"SourceType::TPI" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"InputFilePath::$InputFilePath" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"WriteType::XLSX" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"OutputPath::$OutputFolder" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	debugTPC $ConvertProps
	
	chkSuccess
}

# Write new vector sheet format
Function writeVectorSheet{
	# Check if Techpack installer file exists
	if((-not (Test-Path $convertVector)) -or (-not ([IO.Path]::GetExtension($convertVector) -eq ".xlsx"))){
		Write-Host "`n`Model-T DOES NOT EXIST or NOT OF .XLSX TYPE`n"
		exit
	}

	$convertVector = $convertVector.Substring($convertVector.LastIndexOf("\") + 1)
	
	$OutputFolder = $DebugFolder + "\$convertVector"
	$OutputFolder = $OutputFolder.replace(".xlsx","") + "_VECTOR"
	$InputFilePath = "$pwd" + "\$convertVector"
	
	if(Test-Path $OutputFolder){
		Remove-Item -Path $OutputFolder -recurse
	}
	New-Item -ItemType directory -Path $OutputFolder | Out-Null
	Write-Host "`n`t`t`** WRITING NEW VECTOR SHEET **"
	"--Create new vector sheet" | Out-File -FilePath $ConvertProps -Encoding ASCII
	"ModuleName::Debug.convertVector" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"SourceType::LEGACY_XLSX" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"InputFilePath::$InputFilePath" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	"OutputPath::$OutputFolder" | Out-File -FilePath $ConvertProps -Encoding ASCII -Append
	debugTPC $ConvertProps
	
	chkSuccess
}

# MAIN
# Set constants
$DebugFolder = "$pwd" + "\Debug"
$ConvertProps = "$pwd" + "\debugProps"

# Check arguments
if((($makeXls -eq "") -and ($convertVector -eq "")) -or (($makeXls -ne "") -and ($convertVector -ne ""))){
	usage
}
else{
	if(-not (Test-Path $DebugFolder)){
		New-Item -ItemType directory -Path $DebugFolder | Out-Null
	}
	if($makeXls -ne ""){
		convertTP
	}
	elseif($convertVector -ne ""){
		writeVectorSheet
	}
	else{
		usage
	}
}


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
# 	Name    : encryptDecrypt.ps1
# 	Date    : 01/02/2018
# 	Revision: 1.1
# 	Purpose : Script to use encrypt/decrypt function
#
# 	Usage   : encryptDecrypt.ps1 -[encrypt|decrypt] <full path to package>
# *************************************************************************

# Check arguments
param(
	[string]$encrypt = "",
	[string]$decrypt = ""
)

# Set config file path
$ConfigFilePath = "$pwd" + "\EncDecConfig"

# Trigger the java process
Function trigger{
	java -cp libs/* com.ericsson.eniq.tpc.TPC "$args"
}

# Check the package specified
Function checkPackage{
	if((-not (Test-Path $args)) -or (-not ([IO.Path]::GetExtension($args) -eq ".tpi"))){
		Write-Error "`n`Path provided is not correct`n"
		exit
	}
}

# Encrypt given package
Function encryptPackage{
	"--Encryption" | Out-File -FilePath $ConfigFilePath -Encoding ASCII
	"ModuleName::Encryption.encryptPackage" | Out-File -FilePath $ConfigFilePath -Encoding ASCII -Append
	"Package::$args" | Out-File -FilePath $ConfigFilePath -Encoding ASCII -Append
	trigger $ConfigFilePath
}

# Decrypt given package
Function decryptPackage{
	"--Decryption" | Out-File -FilePath $ConfigFilePath -Encoding ASCII
	"ModuleName::Encryption.decryptPackage" | Out-File -FilePath $ConfigFilePath -Encoding ASCII -Append
	"Package::$args" | Out-File -FilePath $ConfigFilePath -Encoding ASCII -Append
	trigger $ConfigFilePath
}

############################################ MAIN ##########################################
#Validate arguments
if(($encrypt -ne "" -and $decrypt -eq "") -or ($encrypt -eq "" -and $decrypt -ne "")){
	if($encrypt -ne ""){
		checkPackage $encrypt
		encryptPackage $encrypt
	}
	else{
		checkPackage $decrypt
		decryptPackage $decrypt
	}
}
else{
	Write-Error "`n`Incorrect arguments"
	exit
}

#!/bin/bash

if [ "$2" == "" ]; then
    	echo usage: $0 \<Branch\> \<RState\>
    	exit -1
else
	versionProperties=install/version.properties
	theDate=\#$(date +"%c")
	module=$1
	echo "module :${module}"
	branch=$2
	echo "branch :${branch}"
	workspace=$3
	#echo "workspace :$workspace"
	echo "WORKSPACE :${WORKSPACE}"
	#echo "pwd"
fi

function getProductNumber {
       # product=`cat /build.cfg | grep $module | grep $branch | awk -F " " '{print $3}'`
	    product=`cat ${WORKSPACE}/workspace/TPC_Build_Automation_test/build.cfg | grep $module | grep $branch | awk -F " " '{print $3}'`
		echo "product :$product"

}




function setRstate {

        #revision=`cat /build.cfg | grep $module | grep $branch | awk -F " " '{print $4}'`
		revision=`cat ${WORKSPACE}/workspace/TPC_Build_Automation_test/build.cfg | grep $module | grep $branch | awk -F " " '{print $4}'`
		echo "revision :${revision}"
 
       	if git tag | grep $product-$revision; then
	        rstate=`git tag | grep $revision | tail -1 | sed s/.*-// | perl -nle 'sub nxt{$_=shift;$l=length$_;sprintf"%0${l}d",++$_}print $1.nxt($2) if/^(.*?)(\d+$)/';`
			echo "rstate :${rstate}"
        else
                ammendment_level=01
                rstate=$revision$ammendment_level
				echo "ammendment R state :${rstate}"
        fi
	echo "Building R-State:$rstate"

}

function appendRStateToPlatformReleaseXml {

		#versionXml="src/resources/version/release.xml"
		versionXml="${WORKSPACE}/workspace/TPC_Build_Automation_test/src/resources/version/release.xml"
		
		if [ ! -e ${versionXml} ] ; then
			echo "version xml file is missing from build: ${versionXml}"
			exit -1
		fi

		#mv /src/resources/version/release.xml src/resources/version/release.${rstate}.xml
		mv ${WORKSPACE}/workspace/TPC_Build_Automation_test/src/resources/version/release.xml ${WORKSPACE}/workspace/TPC_Build_Automation_test/src/resources/version/release.${rstate}.xml

}


function nexusDeploy {
	
	RepoURL=https://arm1s11-eiffel013.eiffel.gic.ericsson.se:8443/nexus/content/repositories/assure-releases
	
	GroupId=com.ericsson.eniq.TPC
	ArtifactId=TPC_Delivery
	
	path=`find ${WORKSPACE}/workspace/TPC_Build_Automation_test/target/ -name TPC_Delivery_*`
	
	echo "Path :$path"
	package=` awk -F"/" '{print $NF}' <<< $path`
    echo "package :$package"
	file=` awk -F"_" '{print $NF}' <<< $package`
	echo "file :$file"
	rstate_1=` awk -F"." '{print $1}' <<< $file`
	echo "rstate_1:$rstate_1"
	echo "****"	
	#Deploying the zip / as TPC.zip to Nexus....
	echo "Deploying the $package to Nexus...."
       # mv target/$zipName_*.zip target/$zipName_*.zip
	echo "****"	

  	mvn -B deploy:deploy-file \
	        	-Durl=${RepoURL} \
		        -DrepositoryId=assure-releases \
		        -DgroupId=${GroupId} \
		        -DartifactId=${ArtifactId} \
				-Dversion=${rstate_1} \
		        -Dfile=target/${package}
		         
}

#getProductNumber
#setRstate
#git checkout $branch
#git pull origin $branch
#appendRStateToPlatformReleaseXml


#add maven command here
#/proj/eiffel004_config/fem156/slaves/RHEL_ENIQ_STATS/tools/hudson.tasks.Maven_MavenInstallation/Maven_3.0.5/bin/mvn exec:exec
mvn clean install

nexusDeploy 

rsp=$?

if [ $rsp == 0 ]; then
  product="CXP9035524"
  git tag $product-$rstate_1
  git pull
  git push origin $product-$rstate_1

fi

exit $rsp



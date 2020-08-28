//============================================================================
// Name        : main.cpp
// Author      : SergeyTyagushev
// Version     :
// Copyright   : Your copyright notice
// Description : Bootloader
//============================================================================

#include <iostream>

#include "SerialPort.h"
#include "bootloader.h"

#include <cstdio>


using namespace std;

void readfl();

int select_input(int hlim, string str) {

	int i = -1;
	while (i < 0 || i > hlim) {
		cout << str;
		cin >> i;
		if (std::cin.fail()) {
			std::cin.clear();
			std::cin.ignore(32767, '\n');
			std::cout << "Invalid input.  Please try again.\n";
			i = -1;
		};
	}

	return i;
}



int main() {
START:
	SerialPort  Port ;
	bootloader  bl(&Port);
	int res = -1;

	cout << "	***********MPCH LOADER************" << endl;

	Port.setPortName();
	if (Port.Open() == -1)
		return 0;

LOADERSEL:

	cout << endl;
    cout << "	[0] Exit	  " << endl;
	cout << "	[1] Use MPCH bootloader" << endl;
	cout << "	[2] Use MCU 1986VE91T bootloader" << endl;
	cout << "	[3] Test Modbus device " << endl;
	cout << "	[4] Close port " << endl;

	res = select_input(5, "Select action ... ");

	switch (res) {
	case 0:
		return 0;
	case 1:
		break;
	case 2:
		if (bl.getNativeLoader() == -1) goto LOADERSEL;
		break;
	case 3:
		if (bl.getModBusLoader() == -1) goto LOADERSEL;
		break;
	case 4: Port.Close(); goto START;
	default:
		return 0;
	}

BOOTMENU:

	if(bl.getLoaderID()==-1) goto LOADERSEL;;

	cout<<endl;
    cout << 	 "BOOT MENU:    "<<endl;
    cout << "	[0] Exit	  " << endl;
	cout << "	[1] Flash     " << endl;
	cout << "	[2] Verify    " << endl;
	cout << "	[3] Download  " << endl;
	cout << "	[4] Reboot MCU" << endl;
	cout <<endl;

	res = select_input(4, "Set action ... ");

	switch(res){
	case 0:
		return 0;
	case 1:
		cout<<endl<<"WRITING IMAGE TO DEVICE!"<<endl;
		if(bl.readHexFile(bl.vcFileHexStrg, &(bl.iFlashStartAdr), "")==-1)return 0;
		if(bl.writeImage(bl.vcFileHexStrg, bl.iFlashStartAdr )==-1) return 0;
		cout<<endl<<"VERIFYING IMAGES!"<<endl;
		if(bl.readImage  (bl.vcDevHexStrg , bl.vcFileHexStrg.size(),bl.iFlashStartAdr)==-1) return 0;
		   bl.cmprImages(bl.vcDevHexStrg , bl.vcFileHexStrg );
		break;
	case 2:
		cout<<endl<<"VERIFYING IMAGES!"<<endl;
		if(bl.readHexFile(bl.vcFileHexStrg, &(bl.iFlashStartAdr), "")==-1)return 0;
		if(bl.readImage  (bl.vcDevHexStrg , bl.vcFileHexStrg.size(),bl.iFlashStartAdr)==-1) return 0;
		bl.cmprImages(bl.vcDevHexStrg , bl.vcFileHexStrg );
		break;
	case 3:
		break;
	case 4: bl.restartDevice(); Port.Close(); goto START;
	}

	cout<<endl;
    cout << "[0] Exit	   " << endl;
	cout << "[1] BOOT MENU " << endl;
	cout << "[2] Reboot MCU" << endl;
	cout<<endl;


	res = select_input(2, "Set action ... ");

	switch(res){
	case 0: return 0;
	case 1: goto BOOTMENU;
	case 2: bl.restartDevice(); Port.Close(); goto START;
	};

END:
	Port.Close();

	return 0;

}

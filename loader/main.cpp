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



int main(int argc, char* argv[]) {
START:
	SerialPort  Port ;
	bootloader bl(&Port);
	int res = -1;

	if (argc > 1){
		int bdr = stoi(argv[2]);
		int adr = stoi(argv[3]);

		cout<<"Port name:  "<< argv[1]<<endl;
		cout<<"Port speed: "<< bdr <<endl;
		cout<<"Modbus adr: "<< adr <<endl;
		cout<<"Mode: "<<argv[4]<<endl;
		cout<<"file: "<<argv[5]<<endl;

		Port.name = argv[1];

		if (Port.Open(bdr) == -1) return 0;
		bl.getModBusLoader(adr, true);
		if(bl.getLoaderID()==-1) return 0;

		if ( ((string) argv[4]).find("reset") == 0) {
			cout << "RESETTING DEVICE!" << endl;
			bl.restartDevice();
	        return 0;
			};

		bl.readHexFile(argv[5]);

		if ( ((string) argv[4]).find("flash") == 0) {
			cout << "WRITING IMAGE TO DEVICE!" << endl;
			if (bl.writeImage() == -1) return 0;
			bl.verifyImage();
		};

		if ( ((string) argv[4]).find("verify") == 0 ) {
			cout<<"VERIFYING IMAGES!"<<endl;
			bl.verifyImage();
		}

		if ( ((string) argv[4]).find("reboot") == 0 ) {
			bl.restartDevice(); Port.Close();
		}

		return 0;
	}

	cout << "	***********MPCH LOADER************" << endl;

	Port.setPortName();
	if (Port.Open(0) == -1)
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
		if (bl.getModBusLoader(0, false) == -1) goto LOADERSEL;
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
		if(bl.readHexFile("")==-1)return 0;
		if(bl.writeImage()==-1) return 0;
		cout<<endl<<"VERIFYING IMAGES!"<<endl;
		bl.verifyImage();
		break;
	case 2:
		cout<<endl<<"VERIFYING IMAGES!"<<endl;
		if(bl.readHexFile("")==-1)return 0;
		bl.verifyImage();
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


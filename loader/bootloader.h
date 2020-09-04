/*
 * bootloader.h
 *
 *  Created on: 5 мая 2019 г.
 *      Author: sergey
 */

#ifndef BOOTLOADER_H_
#define BOOTLOADER_H_

#include "SerialPort.h"
#include <vector>

namespace std {

class bootloader {


public:


	bootloader(SerialPort * port);
	virtual ~bootloader();
	SerialPort * Port;

	int getModBusLoader(int adr,  bool getLoader);
	int getNativeLoader();
	int getLoaderID();
	int readHexFile (string path);
	int writeHexFile(string path);
	int verifyImage();
	int writeImage();

	int eraseFlash();
	int restartDevice();

private:

	int readImage (int size);
	int cmprImages();

	 vector <char> vcDevHexStrg; // Данные cчитанные из устройства файла
	 vector <char> vcFileHexStrg; // Данные из файла
	 int iFlashStartAdr=0; // базовый адрес прошивки из файла


	enum  resState{
	       OK            =  0,
	       OpenFileError = -1,
	       LineStartError= -2,
	       CRCError      = -3,
	       BaseAdrEror   = -4,
	       ShiftAdrError = -5,
	       EndFileError  = -6,
	       ImageEmpty    = -7,
	       PortIsClose   = -8,
	       TimeOut       = -9,
	       canceled      = -10,
	       FileNotFound  = -11,
	       LoaderNotFound = -12,
	       Done          = -13,
	       EMPTY         =  255
	   };
};

} /* namespace std */

#endif /* BOOTLOADER_H_ */

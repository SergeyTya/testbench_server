/*
 * SerialPort.h
 *
 *  Created on: 4 мая 2019 г.
 *      Author: sergey
 */

#ifndef SERIALPORT_H_
#define SERIALPORT_H_

#include <string>

class SerialPort {

public:
	std::string name;

	SerialPort();
	virtual ~SerialPort();

	void setPortName();
	 int Open(int bdr);
	 int Close();
	 bool isOpen();
	 bool isClose();
	 int Write(const char *, int);
	 int Read (char [], int);
	 std::string readAll();

	 int getModBusId(int);

	 bool waitForReadyRead(int dly);
	 bool waitForReadyRead(int dly, int size);

	 int setBaudRate(int);
	 int getBaudRate();

	 int fd;

private:

};

#endif /* SERIALPORT_H_ */

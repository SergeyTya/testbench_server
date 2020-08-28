/*
 * SerialPort.cpp
 *
 *  Created on: 4 мая 2019 г.
 *      Author: sergey
 */

#include "SerialPort.h"

#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <dirent.h>
#include <string.h>  /* String function definitions */
#include <unistd.h>  /* UNIX standard function definitions */
#include <fcntl.h>   /* File control definitions */
#include <errno.h>   /* Error number definitions */
#include <termios.h> /* POSIX terminal control definitions */
#include <list>
#include <sys/ioctl.h>


using namespace std;

SerialPort::SerialPort() {
	// TODO Auto-generated constructor

	fd = -1;
	this->name = "";
}

SerialPort::~SerialPort() {
	// TODO Auto-generated destructor stub
	close(fd);
}

void SerialPort::setPortName() {

	int n;
	struct dirent ** namelist;
	struct dirent ** namelist2;

	list<string> comList;
	comList.push_back("Enter port name");

	const char* sysdir = "/sys/class/tty/";

	// Scan through /sys/class/tty - it contains all tty-devices in the system
	n = scandir(sysdir, &namelist, NULL, NULL);
	if (n < 0)
		perror("scandir");
	else {
		while (n--) {
			// Construct full absolute file path
			string devicedir = sysdir;
			devicedir += namelist[n]->d_name;
			devicedir += "/device";
			// Scan for port_number file
			int i = scandir(devicedir.c_str(), &namelist2, NULL, NULL);
			if (i > 0) {
				while (i--)
					if (strcmp(namelist2[i]->d_name, "port_number") == 0) {
						comList.push_back(namelist[n]->d_name);
						free(namelist2[i]);
					}
				free(namelist2);
			}
			free(namelist[n]);
		}
		free(namelist);
	}

	int i = 0;
	for (list<string>::iterator it = comList.begin(); it != comList.end();
			it++) {
		cout << "	[" << i << "] " << (*it) << endl;
		i++;
	};

	i = -1;
	while (i < 0 || i > comList.size() - 1) {
		cout << "Select port name ... " ;
		cin >> i;
		if (std::cin.fail()) {
			std::cin.clear();
			std::cin.ignore(32767, '\n');
			std::cout << "Invalid input.  Please try again.\n";
			i = -1;
		}
	};

	if (i != 0) {
		list<string>::iterator it = comList.begin();
		advance(it, i);
		this->name = (*it);
	} else {
		cout << "Enter port name ... ";
		cin >> this->name;
	};

	this->name = "/dev/" + this->name;
}

int SerialPort::Open() {

	struct termios tty;

	if (fd != -1)
		this->Close();

	fd = open(this->name.c_str(), O_RDWR | O_NOCTTY | O_SYNC); //O_NDELAY);
	if (fd == -1) {
		string msg = "Unable to open port " + name;
		perror(msg.c_str());
		return -1;
	} else {
		fcntl(fd, F_SETFL, 0);
		memset(&tty, 0, sizeof tty);

		if (tcgetattr(fd, &tty) != 0) {
			string msg = "Unable to config port " + name;
		    perror(msg.c_str());
			return -1;
		}

		cout<<"	[0] 9600 "<<endl;
		cout<<"	[1] 38400"<<endl;
		cout<<"	[2] 115200"<<endl;
		cout<<"	[3] 230400"<<endl;
		cout<<"	[4] 406000"<<endl;
		int i=-1;

		while (i < 0 || i > 4) {
				cout<<"Select speed ... ";
				cin >> i;
				if (std::cin.fail()) {
					std::cin.clear();
					std::cin.ignore(32767, '\n');
					std::cout << "Invalid input.  Please try again.\n";
					i = -1;
				}
		}

		int spd[5] = { B9600,  B38400, B115200, B230400, B460800 };

		cfsetospeed(&tty, spd[i]);
		cfsetispeed(&tty, spd[i]);

		tty.c_cflag |= (CLOCAL | CREAD);    /* ignore modem controls */
		    tty.c_cflag &= ~CSIZE;
		    tty.c_cflag |= CS8;         /* 8-bit characters */
		    tty.c_cflag &= ~PARENB;     /* no parity bit */
		    tty.c_cflag &= ~CSTOPB;     /* only need 1 stop bit */
		    tty.c_cflag &= ~CRTSCTS;    /* no hardware flowcontrol */

		    /* setup for non-canonical mode */
		    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
		    tty.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
		    tty.c_oflag &= ~OPOST;

		    /* fetch bytes as they become available */
		    tty.c_cc[VMIN] = 1;
		    tty.c_cc[VTIME] = 1;

		    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
		        printf("Error from tcsetattr: %s\n", strerror(errno));
		        return -1;
		    }

	}

	return 0;
}

int SerialPort::Write(const char * buff, int len){

	int res =write(fd, buff, len);
	if(res!=len or res==-1) perror("Serial port error:");
	return res;
}

int SerialPort::Read( char * buf, int len){

	int res=0;
	int bytes;
	ioctl(fd, FIONREAD, &bytes) ;
	if(bytes!= len) {cout<<bytes<<endl; return -1;}
	if( read(fd, buf, len) ==-1 )       {perror("Serial port error"); return -1;}
	return res;
}

int SerialPort::Close() {

	close(fd);
	fd = -1;
	return 0;
}

bool SerialPort::isClose() {
	if (fd == -1)
		return true;
	return false;
}

bool SerialPort::isOpen() {
	if (fd == -1)
		return false;
	return true;
}

bool SerialPort::waitForReadyRead(int timeout){

	int bytes=0;
	int bts=-1;
	int i=0;

	while(i<timeout){
			bts=bytes;
			usleep(1000);
			if(ioctl(fd, FIONREAD, &bytes)==-1) perror("Serial port error");
			if(bytes==bts){i++;}else{i=0;};
		}

	if(bytes>0) return true;
	return false;
}

bool SerialPort::waitForReadyRead(int timeout , int size){

	int bytes=0;
	int bts=-1;
	int i=0;

	while(i<timeout && bytes!=size){
		bts=bytes;
		usleep(1000);
		if(ioctl(fd, FIONREAD, &bytes)==-1) perror("Serial port error");
		if(bytes==bts){i++;}else{i=0;};
	}

	if(bytes==size) return true;

	return false;

}


string SerialPort::readAll(){

	int bytes=0;
	char buf[256];

	string res="";

	if(ioctl(fd, FIONREAD, &bytes)==-1) {perror("Serial port error"); return "";}
	if(read(fd, &buf, bytes)==-1)       {perror("Serial port error"); return "";}
	res.assign(buf, bytes);
	return res;

}

int SerialPort::setBaudRate(int brate){

	struct termios options;

	/*
	 * Get the current options for the port...
	 */

	tcgetattr(fd, &options);

	/*
	 * Set the baud rates to 19200...
	 */

	cfsetispeed(&options, brate);
	cfsetospeed(&options, brate);

	/*
	 * Enable the receiver and set local mode...
	 */

	options.c_cflag |= (CLOCAL | CREAD);

	/*
	 * Set the new options for the port...
	 */

	tcsetattr(fd, TCSANOW, &options);

	return 0;
}

int SerialPort::getBaudRate(){

	struct termios options;
	uint res;

		/*
		 * Get the current options for the port...
		 */

		tcgetattr(fd, &options);

		/*
		 * Set the baud rates to 19200...
		 */

	res = cfgetispeed(&options);

	return res;
}




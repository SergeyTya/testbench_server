/*
 * bootloader.cpp
 *
 *  Created on: 5 мая 2019 г.
 *      Author: sergey
 */
#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <dirent.h>
#include <list>
#include <fcntl.h>
#include <vector>
#include <sstream>
#include <iomanip>
#include <termios.h>

//#include <fstream>

#include "crc16.h"
#include "bootloader.h"

namespace std {


template<typename T>
std::string int_to_hex(T i) {
	std::stringstream stream;
	stream << "0x" << std::setfill('0') << std::setw(sizeof(T) * 2) << std::hex<< i;
	return stream.str();
}


bootloader::bootloader(SerialPort * port) {
	// TODO Auto-generated constructor stub
	Port = port;
	//vcDevHexStrg = new vector <char>;
	//vcFileHexStrg = new vector <char>;
}

bootloader::~bootloader() {
	// TODO Auto-generated destructor stub
}

int bootloader::verifyImage(){

	if( readImage(vcFileHexStrg.size()) == -1) return -1;
	cmprImages();
	return 0;
}

int bootloader::getModBusLoader(int adr=0, bool getLoader=false) {
	//QByteArray  res;
	string str = "";

	if (adr==0 or adr>255) {
		adr = -1;
		while (adr < 1 || adr > 255) {
			cout << "Enter Modbus address [1-255] ... ";
			cin >> adr;
			if (std::cin.fail()) {
				std::cin.clear();
				std::cin.ignore(32767, '\n');
				std::cout << "Invalid input.  Please try again.\n";
				adr = -1;
			}
		}
	}

	char * req = new char[255] { static_cast<char>(adr), 0x2b, 0xe, 0x1, 0x1, 0,
			0 };

	if (Port->isClose())
		return -1;
	cout << "Searching ModBus device at address " << adr << " ... ";

	crc16::usMBCRC16(req, 5);
	Port->readAll();
	if (Port->Write(req, 5 + 2) == -1)
		return -1;
	while (Port->waitForReadyRead(100)) {
		str += Port->readAll();
	};
	if (str.length() < 55) {
		cout << "Timeout" << endl;
		return -1;
	} else {
		cout <<"ok"<<endl;
		cout << "Device: " << str.substr(10, 8)  << endl;
		cout << "Info1 : " << str.substr(32, 10) << endl;
		cout << "SW    : " << str.substr(44, 9)  << endl;
	};

	cout.flush();

	free(req);

SELECT:
	if(getLoader==false){
		cout << "Go to MPCH bootloader mode? (y/n) ... ";
		string chs = "";
		cin >> chs;
		if (chs == "n" || chs == "N") {
			return -1;
		} else if (chs == "y" || chs == "Y") {
			;
		} else {
			goto SELECT;
		};
	}
	req = new char[255] { static_cast<char>(adr), 0x06, 0x0, 0x0, 0x77, 0x77 };
	crc16::usMBCRC16(req, 6);
	Port->readAll();
	if (Port->Write(req, 6 + 2) == -1)
		return -1;

	sleep(1);

	free(req);
	return 0;
}
;

int bootloader::getNativeLoader() {

	cout <<endl<<"	Setup 1986VE91T native bootloader" << endl;
	cout       <<"	---------------------------------" << endl<<endl;;

	char cwd[PATH_MAX];
	string path;
	vector<char> image;
	int baseadr;

	if (getcwd(cwd, sizeof(cwd)) != NULL) {
		//printf("Current working dir: %s\n", cwd);
	} else {
		perror("getcwd() error");
		return 1;
	}

	path = cwd;
	path += "/loader.hex";

	//readHexFile(image, &baseadr, path);

	int brate =0;
	int tempbr = Port->getBaudRate();
	Port->setBaudRate(B9600);
	cout << "Synchronization ... ";
	cout.flush();
	char req[512] = { 0, 0, 0 };
	for (int i = 0; i < 512; i++) {
		Port->Write(req, 1);
	};
	sleep(3);
	cout<<"DONE!" << endl;

	switch (tempbr)
	{
	case B9600: brate=9600; break;
	case B38400: brate=38400; break;
	case B115200: brate=115200; break;
	case B230400: brate= 230400; break;
	default : cout<< "Aborted! Unsupported speed!"<<endl; return -1;
	}

	cout << "Set baudRate "<<brate<<" ... ";
	cout.flush();

	/* Скорость передачи */
	req[0] = 'B';
	req[1] = static_cast<char>( brate & 0xff );
	req[2] = static_cast<char>((brate >> 8) & 0xff);
	req[3] = static_cast<char>((brate >> 16) & 0xff);
	req[4] = static_cast<char>(0);
	Port->Write(req, 5);
	sleep(1);

		Port->setBaudRate(tempbr);

	cout<<"DONE!" << endl;

	cout << "Loading RAM boot ... 0%" << endl;
	cout.flush();

	for (uint i = 0; i < (image.size() / 256); i++) {

		req[0] = 'L';
		req[1] = static_cast<char>((baseadr >> 0) & 0xff);
		req[2] = static_cast<char>((baseadr >> 8) & 0xff);
		req[3] = static_cast<char>((baseadr >> 16) & 0xff);
		req[4] = static_cast<char>((baseadr >> 24) & 0xff);
		req[5] = static_cast<char>((256 >> 0) & 0xff);
		req[6] = static_cast<char>((256 >> 8) & 0xff);
		req[7] = static_cast<char>(0x0);
		req[8] = static_cast<char>(0x0);

		if(Port->Write(req, 9)==-1) {
			cout << "	Timeout 1" << endl;
			return -1;
		};
		usleep(1000 * 50);

		for (int k = 0; k < 256; k++)
			req[k] = image[256 * i + k];

		if(Port->Write(req, 256)==-1) {
			cout << "	Timeout 1" << endl;
			return -1;
		};
		usleep(1000 * 300);

		baseadr += 0x100;

		int progres = 100 * (i + 1) / static_cast<int>(image.size() / 256);

		cout << "\x1b[1A" << "\x1b[0J" << "Loading RAM boot ... ";
		cout.flush();
		cout << progres << "%" << endl; //стирание строки
		cout.flush();

	};

	cout << "Starting device ... ";
	cout.flush();
	/*Команда на запуск с адресом таблицы прерываний*/
	req[0] = 'R';
	req[1] = static_cast<char>(0x0);
	req[2] = static_cast<char>(0x0);
	req[3] = static_cast<char>(0x0);
	req[4] = static_cast<char>(0x20);

	if(Port->Write(req, 5)==-1) {
		cout << "Timeout 1" << endl;
		return -1;
	};

	sleep(1);
	Port->readAll();

	cout<<"DONE!" << endl;
	cout.flush();

	return 0;
}

int bootloader::getLoaderID(){

	char req [1];

	cout << "Waiting for bootloader ID ... ";
	cout.flush();

	req[0] = 'I';
	if(Port->Write(req, 1)==-1) {
		cout << "Timeout 1" << endl;
		return -1;
	};

	string str = "";
	while (Port->waitForReadyRead(1000)) {
		str += Port->readAll();
	};
	if (str == "") {
		cout << "Timeout" << endl;
		return -1;
	};

	cout << str << endl;

	return 0;
}

int bootloader::readHexFile(string path) {

	bool endfile = false; //
	int count = 0; // номер записи по счету
	int adrcount = 0; // текущий адрес полученный из номера записи
	int baseadr = 0; // базовый адрес
	int size = 0; // размер данных в одной записи
	int adr = 0;  //смещение адреса от базового
	int type = 0; // тип записи
	int crc = 0;    // crc записи
	string str = ""; // считанная строка
	int res = 0; //возвращаемый резльтат

	vcFileHexStrg.clear();

	struct dirent ** namelist;
	char cwd[PATH_MAX];
	int n = -1;
	list<string> hexfileList;
	char buf[512];

	if (path == "") {

		if (getcwd(cwd, sizeof(cwd)) != NULL) {
			printf("Current working dir: %s\n", cwd);
		} else {
			perror("getcwd() error");
			return 1;
		}

		n = scandir(cwd, &namelist, NULL, NULL);

		if (n < 0)
			perror("scandir");
		else {
			while (n--) {
				string tmp = namelist[n]->d_name;
				if (tmp.length() > 4) {
					string ext = tmp.substr(tmp.length() - 3, 3);
					if (ext == "hex")
						hexfileList.push_back(tmp);
				};
				free(namelist[n]);
			}
			free(namelist);
		}

		if (hexfileList.size() == 0) {
			cout << ".hex files not found" << endl;
			return -1;
		};

		int i = 0;
		for (list<string>::iterator it = hexfileList.begin();
				it != hexfileList.end(); it++) {
			cout << "	[" << i << "] " << (*it) << endl;
			i++;
		};

		i = -1;
		while (i < 0 || i > hexfileList.size() - 1) {
			cout << "Select hex file ... ";
			cin >> i;
			if (std::cin.fail()) {
				std::cin.clear();
				std::cin.ignore(32767, '\n');
				std::cout << "Invalid input.  Please try again.\n";
				i = -1;
			}
		};

		list<string>::iterator it = hexfileList.begin();
		advance(it, i);
		path = cwd;
		path += "/" + (*it);
	};
/*
	fstream fs(path, fstream::in);
	if (!fs.is_open()) {
		perror("File IO error");
		return -1;
	};

	while (!fs.getline(buf, 256).eof()) {
*/

	FILE *file = fopen (path.c_str(), "r");
	if (file == NULL){
		perror("File IO error");
				return -1;
	};

	while (fgets(buf,sizeof(buf),file)) {

		str.assign(buf, 256);

		if (str.find(":") != 0) {
			cout << "Line start error" << endl;
			res = LineStartError;
			break;
		};
		size = stoi(str.substr(1, 2), 0, 16) + 4; // +4 так как служебная информация
		crc = 0;

		char * fulldata = new char[size];

		for (int i = 0; i < size; i++) {
			fulldata[i] = stoi(str.substr(1 + i * 2, 2), 0, 16);
			crc += fulldata[i];
		};
		crc = 0xff & (0 - crc);

		//Проверка CRC
		if (crc != stoi(str.substr(3 + (size - 1) * 2, 2), 0, 16)) {
			cout << "Line CRC Error" << endl;
			res = CRCError;
			break;
		};

		// заполняю атрибуты
		size = fulldata[0];
		type = fulldata[3];
		adr = (fulldata[1] << 8) + fulldata[2];

		/*Проверяю тип записи*/
		if (type == 1) //Конец файла
				{
			endfile = true;
			// дополняем до размера кратного 256
			while ((static_cast<uint>(vcFileHexStrg.size() / 256)) * 256
					!= vcFileHexStrg.size()) {
				vcFileHexStrg.push_back(static_cast<char>(0xFF));
			};
			cout << "Reading Image from file ... " << vcFileHexStrg.size()
					<< " byte read!" << endl;
			break;
		};
		if (type == 5)
			continue;		          // иногда попадается
		if (type == 4) //Задание базового адреса
				{
			baseadr = (fulldata[4] << 24) + (fulldata[5] << 16); //новый базовый адрес
			if (adrcount == 0) //если в начале файла
					{
				adrcount = baseadr;
				iFlashStartAdr = baseadr;
			} else //если в середине файда
			{
				if (baseadr < adrcount) {
					// _mBDEBUG("Ошибка целостности адреса 1");
					cout << "Address check fault" << endl;
					res = BaseAdrEror;
					break;
				};
				for (int i = 0; i < (baseadr - adrcount); i++) // заполняю дырку
						{
					vcFileHexStrg.push_back(static_cast<char>(0xFF));
				};
				adrcount = baseadr;
			};
			continue;
		};

		int tmp = ((stoi(str.substr(3, 4), 0, 16)) & 0xFFFF)
				- (adrcount & 0xFFFF);

		if (tmp != 0) {
			if (tmp < 0) {
				cout << "line address err" << endl;
				res = ShiftAdrError;
				break;
			}
			for (int i = 0; i < tmp; i++) //Добовление пропущенных байт
					{
				vcFileHexStrg.push_back(static_cast<char>(0xFF));
			};

			adrcount += tmp;
		};

		/*добавляем данные в буфер*/
		for (int i = 0; i < size; i++)vcFileHexStrg.push_back(fulldata[4 + i]);
		/*счетчик адреса*/
		adrcount += size;
		/*счетчик строк*/
		count++;

		delete(fulldata);
	};

	fclose(file);

	/* если небыло последней записи - ошибка*/
	if (!endfile && res == OK) {
		cout << "Error file end not found" << endl;
		res = EndFileError;
	};
	/* если завершено с ошибкой*/
	if (res != OK) {
		cout << "File read Error" << endl;
		vcFileHexStrg.clear();
		return res;
	};

	return vcFileHexStrg.size();
}

int bootloader::readImage(int size) {

	char buf[512];

	string str = "";

	vcDevHexStrg.clear();

	buf[0] = 'A';
	Port->Write(buf, 1);

	usleep(300);

	buf[0] = 0;
	buf[1] = 0;
	buf[2] = static_cast<char>(iFlashStartAdr >> 16);
	buf[3] = static_cast<char>(iFlashStartAdr >> 24);

	if (Port->Write(buf, 4) == -1)
		return -1;

	while (Port->waitForReadyRead(300)) {
		str += Port->readAll();
	};
	if (str == "") {
		cout << "Timeout 0" << endl;
		return -1;
	};

	cout << "Reading Image from device ... 0%" << endl;

	for (uint i = 0; i < static_cast<uint>(size / 256); i++) {

		buf[0] = 'V';

		if (Port->Write(buf, 1) == -1) {
			cout << "Timeout 1" << endl;
			return -1;
		};

		if (Port->waitForReadyRead(50, 256) == false) {
			cout << "Timeout 2" << endl;
			return -1;
		};

		if (Port->Read(buf, 256) == -1) {
			cout << "Timeout 3" << endl;
			return -1;
		};

		for (int k = 0; k < 256; k++) vcDevHexStrg.push_back(buf[k]);

		int progres = 100 * (i + 1) / static_cast<int>(size / 256);

		//cout << "\x1b[1A" << "\x1b[0J" << "Reading Image from device ... ";
		//cout << progres << "%" << endl; //стирание строки
		cout << "Reading Image from device ... "<<progres << "%" << endl;
		cout.flush();
	};

	//cout << "\x1b[1A" << "\x1b[0J";
	cout << "Reading Image from device ..." << vcDevHexStrg.size() << " byte read!"
			<< endl;

	return 0;
};

int bootloader::cmprImages() {

	bool res = false;
	uint cnt = 0;

	for (uint i = 0; i < vcDevHexStrg.size(); i++) {
		cnt = i;
		uint8_t r1 = vcDevHexStrg.at(i);
		uint8_t r2 = vcFileHexStrg.at(i);
		if ( r1!= r2) {
			res = true;
		};

	if (res == true) {
		cout << "Error: Image verify fault! " << endl;
		cout << "	Image1[" << cnt << "]="
				<< int_to_hex(static_cast<int>(vcDevHexStrg.at(cnt))) << endl;
		cout << "	Image2[" << cnt << "]="
				<< int_to_hex(static_cast<int>(vcFileHexStrg.at(cnt))) << endl;

		res=false;
	   return -1;
		};

	};

	cout << "Image verify done! " << endl;
	return 0;
}

int bootloader::writeImage(){

	char buf[512];
	string str = "";

	buf[0] = 'A';
	Port->Write(buf, 1);

	usleep(300);

	buf[0] = 0;
	buf[1] = 0;
	buf[2] = static_cast<char>(iFlashStartAdr >> 16);
	buf[3] = static_cast<char>(iFlashStartAdr >> 24);

	if (Port->Write(buf, 4) == -1)
		return -1;

	while (Port->waitForReadyRead(300)) {
		str += Port->readAll();
	};
	if (str == "") {
		cout << "Timeout 0" << endl;
		return -1;
	};

	if(bootloader::eraseFlash()<0) return -1;

	cout << "Writing Image to device ... 0% " << endl;

	buf[0] = 'A';
		Port->Write(buf, 1);

		usleep(300);

		buf[0] = 0;
		buf[1] = 0;
		buf[2] = static_cast<char>(iFlashStartAdr >> 16);
		buf[3] = static_cast<char>(iFlashStartAdr >> 24);

	if (Port->Write(buf, 4) == -1)
		return -1;

	while (Port->waitForReadyRead(1000)) {
		str += Port->readAll();
	};
	if (str == "") {
		cout << "Timeout 0" << endl;
		return -1;
	};


	 for (int i = 0; i < vcFileHexStrg.size() / 256; i++) {

		buf[0] = 'P';

		if (Port->Write(buf, 1) == -1)
			return -1;

		for(int j=0;j<256;j++){
			buf[j]=vcFileHexStrg.at(j+256*i);
		}

		if(Port->Write(buf, 256)==-1) {
			cout << "Timeout 1" << endl;
						return -1;
		};

		str="";

		if (!Port->waitForReadyRead(500, 1))  {
			cout << "Timeout2" << endl;
			return -1;
		};
		 Port->readAll();

		 int progres= 100*(i+1)/static_cast<int>(vcFileHexStrg.size()/256);
		 //cout << "\x1b[1A" << "\x1b[0J" << "Writing Image to device ... ";
		 //cout << progres << "%" << endl; //стирание строки
		 cout << "Writing Image to device ... " << progres << "%" << endl;
		 cout.flush();

	};

	return 0;
}

int bootloader::eraseFlash(){

	char buf[512];
	string str = "";

	cout<<"Erase MCU flash ... ";

	buf[0]='E';
	if (Port->Write(buf, 1) == -1)
			return -1;

	while (Port->waitForReadyRead(300)) {
		str += Port->readAll();
	};

	if(str!="EOK") {cout << "error"<<endl; return -1;};

	cout<<"ok"<<endl;

	return 0;
}

int bootloader::restartDevice(){


	char buf[512];
		string str = "";

		cout<<"Restart MCU ... ";

		buf[0]='R';
		buf[1]='R';
		if (Port->Write(buf, 2) == -1)
				return -1;

		while (Port->waitForReadyRead(300)) {
			str += Port->readAll();
		};

		cout<<"ok"<<endl;

		return 0;
}

} /* namespace std */


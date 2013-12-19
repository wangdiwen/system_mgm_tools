./configure --prefix=/usr/local/ajaxterm --port=8022
make
make install

cd /usr/local/ajaxterm/bin
./ajaxterm --demaon

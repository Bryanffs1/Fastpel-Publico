# Sistema de gestión para el préstamo de equipos y control de acceso del laboratorio de ingeniería electrónica (FastPEl)

En el presente repocitorio tuvo como propósito desarrollar un sistema intuitivo que facilitara los procesos de préstamos y devolución de equipos en el laboratorio principal de ingeniería electrónica y el control de acceso con tecnología Near Field Communication (NFC) en el laboratorio de software especializado de la Universidad de Ibagué. 
Su elaboración consto de dos partes, la construcción de un software programado en su mayoría en lenguaje de programación en Python y lenguaje de marcado de hipertexto HTML, el cual se apoyó con CSS y JavaScript; y un hardware que lo constituye una raspberry pi 4, un circuito y componentes electrónicos el cual se complementaron con el software para satisfacer los objetivos planteados y las necesidades de los usuarios que dieron uso a este.

Los contenidos de este repositorio:
  - Códigos fuentes
  - Datasheets
  - Base de datos
  - Requisitos del hardware y software
  - Como instalar y ejecutar el sistema
  - Video tutoriales

## Requisitos del Hardware
### Servidor
Los requisitos necesarios para el correcto funcionamiento del servidor constan de:

- Una CPU con sistema operativo de Ubuntu con Python 3.9.12 y con acceso a internet
- Librerías necesarias
- 3 Gigabyte de RAM mínimo
- 160Gb de memoria del disco duro

### Control de acceso
Los requisitos necesarios para el correcto funcionamiento del control de acceso al laboratorio de ingeniería electrónica constan de:

- Una Raspberry pi 4 modelo B 4GB RAM con sistema operativo recomendado de Raspberry Pi OS (32-bit) con acceso a internet
- Fuente de alimentación USB-C 5V 3A con interruptor de encendido/apagado (para Raspberry pi 4 modelo B)
- Memoria SD samsung PRO Endurance 32GB
- Un módulo NFC RFID-RC522 13.56MHz
- Cerradura eléctrica para puerta marca UHPPOTE
- Fuente de alimentación de 12V dc marca UHPPOTE
- Caja en acrilico con su stiker
- Caja metalica
- Tornilleria para fijar componentes al acrilico y para fijar el acrilico a la pared
- Un Relé de 12 voltios
- Ocho borneras
- Cuatro transistores 2n2222A
- Cuatro Resistencias para configuracion en saturacion de los transistores
- Un diodo rectificador
- Un buzzer de 12v dc
- Dos leds de 12v dc (tipo pilotos)
- Un led de 3.3v dc
- Cableado

### Usuario
Los requisitos necesarios para el correcto funcionamiento de FASTPEL y el control de acceso para el usuario constan de:

  - Un computador con acceso a internet (mejor si es con OS Windows )
  - Pistola lectora de códigos de barras
  - Dispositivo inteligente ACR122U NFC RFID 13.56Mhz de escritura y lectura de tarjetas NFC marca ETEKJOY
  - Tarjetas NFC 13.56MHz para 1K S50 MF1 mi-fare


## Requisitos del Software
  - Ubuntu
  - Python 3.9.12
  - Bases de datos
  - Librerias necesarias

## Como instalar el software
### Servidor
Para el correcto funcionamiento de FastPEL en el servidor, es necesario realizar unos pasos previos antes de iniciar la aplicacion:

**-Instalar las librerias necesarias:**

- PIP
Su instalación en terminal:
```sh
sudo apt install python3-pip
```
- Flask
Su instalación en terminal:
```sh
pip install Flask 
```
Si genera error con itsdangerous al ejecutar el software, degrada itsdangerous y se solucionara:
```sh
pip install itsdangerous==2.0.1
```
- flask_sqlalchemy
Su instalación en terminal:
```sh
pip install Flask-SQLAlchemy
```
- flask_bcrypt
Su instalación en terminal:
```sh
pip install Flask-Bcrypt
```
- _cffi_backend
Su instalación en terminal:
```sh
pip install cffi
```
- flask_login
Su instalación en terminal:
```sh
pip install Flask-Login
```
- flask_mail
Su instalación en terminal:
```sh
pip install Flask-Mail
```
- flask_wtf
Su instalación en terminal:
```sh
pip install Flask-WTF
```
- email_validator
Su instalación en terminal:
```sh
pip install email-validator
```
- Pandas
Su instalación en terminal:
```sh
pip install pandas
```
- IPython
Su instalación en terminal:
```sh
pip install IPython
```
- PIL
Su instalación en terminal:
```sh
pip install Pillow
```
Si genera error con la librería PIL al ejecutar el software, instalar así:
```sh
pip install -U pillow
```
- Sockets (normalmente ya viene por defecto en el sistema)
Su instalación en terminal:
```sh
pip install sockets
```
- key-generator
Su instalación en terminal:
```sh
pip install key-generator
```

-Poner el correo electrónico (Gmail) y contraseña del administrador ya que es necesario para el correcto funcionamiento de algunas funciones, su contraseña será encriptada y no se hará manejo del correo sin su autorización, por ende, no se tiene que preocupar.
Para hacer esta configuración, entre a la carpeta flaskblog luego, abra el archivo "**__ init__.py**" y cambie las variables (sin quitar las comillas):
```sh
'correo_del_administrador'
'contraseña_del_correo_del_administrador' 
```
Guarde y salga.

-Se le da permisos a su cuenta de Gmail que pusiste en el "correo_del_administrador", para esto abre tu cuenta Gmail y ve a "Gestionar tu cuenta de Google" luego le das en "Seguridad" después vas en "Acceso de aplicaciones poco seguras" le das en "Activar el acceso" por último le das si a "Permitir el acceso de apps menos seguras" (esto se realizara la primera vez y cuando se requiera)

-Luego se tiene que poner su IP, para ello entra al archivo "run .py" y donde dice:
```sh 
host='su_IP' 
```
cambia su_IP por su IP (sin quitar las comillas, esto se realizara una unica vez).

**¿Como saber que IP tengo?**

En el terminal se pone "ifconfig" y buscas se IP.
Es necesario que tenga instalada net-tools, en el caso que no se tenga, se puede instalar con el siguiente comando:
```sh 
sudo apt install net-tools
```

-Continuamos creando nuestra base de datos de usuarios, para esto abrimos la terminal y vamos a la carpeta donde está el archivo "run .py", abrimos python3 y desde ahí y ejecutamos las siguientes líneas (esto se realizará una única vez):

```sh 
from flaskblog import db
db.create_all()
```
cerramos python con:
```sh 
exit()
```
-Luego se debe crear dos cuentas en FastPEL, una del administrador y otra de los monitores para esto ejecutamos el software y vamos a "Regístrate", ponemos como nombre ***Administrador*** (obligatorio) luego ingresa un email y una contraseña (no es la contraseña del email, es una nueva contraseña para la cuenta de software); para monitores hacemos lo mismos pasos anteriores con la diferencia de que el nombre será ***Monitores*** (obligatorio, esto se realizará una única vez)

-Finalmente se debe poner la IP y puerto de la(s) raspberry(s) pi del control de acceso en las funciones de ***Controlmanuallaboratorio*** y ***Controllaboratorio*** que se encuentan en el archivo "**routes.py**"
```sh
#--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
 ip_cliente_manual = 'IP'   
 puerto_cliente_manual = 5050
```
```sh
#--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
ip_cliente = 'IP'
puerto_cliente = 5050
```
> **Con esta configuración el software ya está correctamente configurado en el servidor.**

### Control de acceso
**-Instalar las librerias necesarias en la raspberry pi:**

- Selenium version 4.1.3
Su instalación en terminal:
```sh
pip install selenium
```
- Sockets (normalmente ya viene por defecto en el sistema)
Su instalación en terminal:
```sh
pip install sockets
```
- RPi.GPIO
Su instalación en terminal:
```sh
pip instalar RPi.GPIO
```
- mfrc522
Su instalación en terminal:
```sh
pip instalar mfrc522
```

-Modificar la libreria mfrc522 el script **SimpleMFRC522.py** en:
```sh
  codigo
```
por
```sh
 codigo
```
-Activar el SPI de la raspberry pi

-Instalar el driver de chromium para selenium en la ruta "/usr/lib/chromium-browser/chromedriver", se instala asi:
```sh
Sudo apt-get install chromium-chromedriver xvfb
```

-Para configurar la raspberry pi del control de acceso, se deben copiar la carpeta  **run**  en el escritorio de la raspberry pi, luego se  configura la ip de la raspberry pi en el script de **runserver.py**
```sh
ip_servidor = 'IP' 
puerto_servidor = 5050 
```
-Configurar la ruta del control de laboratorio de FastPEL en el script **runapp.py** para selenium:
```sh
driver.get('http://fastpel.unibague.edu.co:8080/Controllaboratorio') 
```
> **Con esta configuración el software ya está correctamente configurado en la raspberry pi.**

### Usuario

> **Con esta configuración el software ya está correctamente configurado en el computador del usuario.**

## Como ejecutar el software
### En el servidor
Para ejecutar el software en el servidor, se tiene que ingresar al servidor por ssh:
```sh
ssh us@xxx.xx.xx.xx
```
Luego se digita su contraseña, una vez ingresamos al servidor, creamos una nueva ventana de la terminal asi:
```sh
screen -S runfastpel
```
luego en la nueva ventana se ingresa en el directorio donde esta el archivo  **runfastpel.sh** y se ejecuta asi:
```sh
Sh rrunffastpel.sh
```
Finalmente salimos de esta ventana precionando los comando ***CTRL+a+d*** a la misma vez, luego salimos de la conexion ssh con **exit**.

### En la raspberry pi
Para ejecutar los script del control de acceso automaticamente al encender la raspberry, se crea un archivo en el directorio siguiente asi:
```sh
sudo nano codigo
```
Luego se escribe lo siguiente y se guarda con CTRL+o (Para eliminar desde la ubicación: sudo rm fastpelrun.desktop ):
```sh
[Desktop Entry]
Name=PiFastpelRun
Exec=codigo
```
Luego se escribe el run.sh con un delay al principio para que carge el sistema al prender y funcione correctamente, este archivo se crea en la carpeta **run**:
```sh
sleep 55
#!/bin/sh

codigo

```
Se dan permisos al run.sh, para ello se va por la terminal al sitio donde está el archivo (carpeta run) y se escribe :
```sh
chmod 777 run.sh
```
Debe quedar en otro color si se ve con "ls" en la terminal.

Despues se agrega el archivo run.sh a las aplicaciones de inicio, para ello vamos a aplicaciones y búscanos inicio, luego abrimos preferencias de las aplicaciones al inicio, buscamos y añadimos nuestra aplicación (nuestro archivo run.sh).

Finalmente se reinicia y automaticamente luego de unos minutos, se ejecuta automaticamente el sistema de control de acceso.

## Funciones de FastPEL
- Registro de usuario nuevo
- Restablecer la contraceña de un usuario
- Modificar datos de un usuario
- Postear informacion para los usuarios (administador y monitores)
- Modificar o eliminar post (administador y monitores)
- Prestamo  (administador y monitores)
- Devolucion (administador y monitores)
- Solicitar equipo (administador y monitores)
- Laboratorios

## *Importante*
Para el correcto funcionamineto del software, hay que tener en cuenta los siguientes puntos:
- Las bases de datos son archivos .csv.
- No se puede modificar los nombres de las bases de datos.
- No se puede modificar las cabeceras de las bases de datos.
- Las bases de datos tienen que estar en una carpeta llamada bases de datos.
- EL contenido de la carpeta src tiene que ir en una carpeta llamada web y creada en la misma direccion que la carpeta base de datos.
- No se pueden utilizar caracteres como la ñ o vocales con tildes.

***
## Autores
#### Universidad de Ibagué
#### Programa de Electrónica
#### Proyecto de Grado

- [Bryan F. Fandiño] - (2420162019@estudiantesunibague.edu.co)
- [Harold F MURCIA] - Tutor

***
[Harold F MURCIA]: <http://haroldmurcia.com>

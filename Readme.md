# Sistema de gestión para el préstamo de equipos y control de acceso del laboratorio de ingeniería electrónica (FastPEl)

El presente repositorio tuvo como propósito desarrollar un sistema intuitivo que facilitara los procesos de préstamos y devolución de equipos en el laboratorio principal de ingeniería electrónica y el control de acceso con tecnología Near Field Communication (NFC) en el laboratorio de software especializado de la Universidad de Ibagué. 
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

- Una CPU con sistema operativo de Ubuntu y con acceso a internet
- 3 Gigabyte de RAM mínimo
- 160Gb de memoria del disco duro

### Control de acceso
Los requisitos necesarios para el correcto funcionamiento del control de acceso al laboratorio de ingeniería electrónica constan de:

- Una Raspberry pi 4 modelo B 4GB RAM con acceso a internet
- Fuente de alimentación USB-C 5V 3A con interruptor de encendido/apagado (para Raspberry pi 4 modelo B)
- Memoria SD samsung PRO Endurance 32GB
- Un módulo NFC RFID-RC522 13.56MHz
- Cerradura eléctrica para puerta marca UHPPOTE
- Fuente de alimentación de 12V dc marca UHPPOTE
- Caja en acrílico con su stiker
- Caja metálica
- Tornillería para fijar componentes al acrílico y para fijar el acrílico a la pared
- Un Relé de 12 voltios
- Ocho borneras
- Cuatro transistores 2n2222A
- Cuatro Resistencias para configuración en saturación de los transistores
- Un diodo rectificador
- Un buzzer de 12v dc
- Dos leds de 12v dc (tipo pilotos)
- Un led de 3.3v dc
- Cableado

### Usuario
Los requisitos necesarios para el correcto funcionamiento de FASTPEL y el control de acceso para el usuario constan de:

  - Un computador con acceso a internet (mejor si es con OS Windows)
  - Pistola lectora de códigos de barras
  - Dispositivo inteligente ACR122U NFC RFID 13.56Mhz de escritura y lectura de tarjetas NFC marca ETEKJOY
  - Tarjetas NFC 13.56MHz para 1K S50 MF1 mi-fare

## Requisitos del Software
### Servidor
Los requisitos necesarios para el software en el servidor son los siguientes:
  - OS Ubuntu
  - Python 3.9.12
  - Bases de datos
  - Librerías necesarias

### Control de acceso
Los requisitos necesarios para el correcto funcionamiento del control de acceso al laboratorio de ingeniería electrónica constan de:
- Sistema operativo recomendado de Raspberry Pi OS (32-bit).

### Usuario
Los requisitos necesarios para el correcto funcionamiento de FASTPEL y el control de acceso para el usuario constan de:
- Controlador para el dispositivo ACR122U NFC RFID
- Software NFC Toolls versión 2.5

## Como instalar el software
### Servidor
Para el correcto funcionamiento de FastPEL en el servidor, es necesario realizar unos pasos previos antes de iniciar la aplicación:

**-Clonar este repositorio**
https://github.com/Bryanffs1/FastPEL.git

-Instalar las librerías necesarias:

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
cambia su_IP por su IP (sin quitar las comillas, esto se realizará una única vez).

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

-Finalmente se debe poner la IP y puerto de la(s) raspberry(s) pi del control de acceso en las funciones de ***Controlmanuallaboratorio*** y ***Controllaboratorio*** que se encuentran en el archivo "**routes.py**"
```sh
#--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
 ip_cliente_manual = 'IP'   
 puerto_cliente_manual = Puerto
```
```sh
#--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
ip_cliente = 'IP'
puerto_cliente = Puerto
```
> **Con esta configuración el software ya está correctamente configurado en el servidor.**

### Control de acceso
**-Instalar las librerías necesarias en la raspberry pi:**

- Selenium versión 4.1.3
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

-Modificar la librería mfrc522 el script **SimpleMFRC522.py** en la línea que define que bus de memoria se leerá de la tarjeta NFC:
```sh
  BLOQUE_DIRECCIONES  = [ 8 , 9 , 10 ]
```
por
```sh
 BLOQUE_DIRECCIONES  = [11 , 12 , 13 ]
```
o por el bus de memoria donde se está grabando la información de la tarjeta NFC.

-Activar el SPI de la raspberry pi

-Instalar el driver de chromium para selenium en la ruta "/usr/lib/chromium-browser/chromedriver", se instala asi:
```sh
Sudo apt-get install chromium-chromedriver xvfb
```

-Para configurar la raspberry pi del control de acceso, se deben copiar la carpeta  **run**  en el escritorio de la raspberry pi, luego se  configura la ip de la raspberry pi en el script de **runserver.py**
```sh
ip_servidor = 'IP' 
puerto_servidor = Puerto 
```
-Configurar la ruta del control de laboratorio de FastPEL en el script **runapp.py** para selenium:
```sh
driver.get('http://fastpel.unibague.edu.co:8080/Controllaboratorio') 
```
> **Con esta configuración el software ya está correctamente configurado en la raspberry pi.**

### Usuario
En la configuración del computador del usuario, es necesario descargar el controlador para el ACR122U NFC RFID, el cual se encuentra en el siguiente enlace:
https://www.acs.com.hk/en/driver/3/acr122u-usb-nfc-reader/

También se necesita instalar el software NFC Toolls versión 2.5 el cual se puede encontrar en el siguiente link:
https://www.wakdev.com/en/apps/nfc-tools-pc-mac.html

Todo estará correctamente instalado a la hora de conectar el dispositivo ACR122U NFC RFID al computador, abrir la aplicación NFC Toolls y que esta reconozca el dispositivo.

> **Con esta configuración el software ya está correctamente configurado en el computador del usuario.**

## Como ejecutar el software
### En el servidor
Para ejecutar el software en el servidor, se tiene que ingresar al servidor por ssh:
```sh
ssh usuario@172.17.92.75
```
Luego se digita su contraseña, una vez ingresamos al servidor, creamos una nueva ventana de la terminal asi:
```sh
screen -S runfastpel
```
luego en la nueva ventana se ingresa en el directorio donde está el archivo  **runfastpel.sh** y se ejecuta asi:
```sh
Sh runfastpel.sh
```
Finalmente salimos de esta ventana presionando los comandos ***CTRL+a+d*** a la misma vez, luego salimos de la conexión ssh con **exit**.

### En la raspberry pi
Para ejecutar los scripts del control de acceso automáticamente al encender la raspberry, se crea un archivo en el directorio siguiente así:
```sh
sudo nano /etc/xdg/autostart/fastpelrun.desktop
```
Luego se escribe lo siguiente y se guarda con CTRL+o (Para eliminar desde la ubicación: sudo rm fastpelrun.desktop ):
```sh
[Desktop Entry]
Name=PiFastpelRun
Exec=/bin/sh /home/pi/Desktop/run/run.sh
```
Luego se escribe el run.sh con un delay al principio para que cargue el sistema al prender y funcione correctamente, este archivo se crea en la carpeta **run**:
```sh
sleep 55
#!/bin/sh

/usr/bin/lxterminal -e /usr/bin/python3 /home/pi/Desktop/run/runserver.py &
sleep 6
/usr/bin/lxterminal -e /usr/bin/python3 /home/pi/Desktop/run/runapp.py 

```
Se dan permisos al run.sh, para ello se va por la terminal al sitio donde está el archivo (carpeta run) y se escribe:
```sh
chmod 777 run.sh
```
Debe quedar en otro color si se ve con "ls" en la terminal.

Después se agrega el archivo run.sh a las aplicaciones de inicio, para ello vamos a aplicaciones y búscanos inicio, luego abrimos preferencias de las aplicaciones al inicio, buscamos y añadimos nuestra aplicación (nuestro archivo run.sh).

Finalmente se reinicia y automáticamente luego de unos minutos, se ejecuta automáticamente el sistema de control de acceso el cual al encender un led de 3.3v conectado directamente a la raspberry pi, significara que el sistema se ejecutó correctamente.

## Tutoriales de funciones de FastPEL
|  Función | Descripción  | Link  |
| :------------ | :------------ | :------------: |
|  Prestamos | Realiza prestamos de equipos del laboratorio de ingeniería electrónica.  | https://youtu.be/ZBBo_RA_zvs  |
| Devoluciones  | Realiza devoluciones de equipos del laboratorio de ingeniería electrónica.  | https://youtu.be/c17JRdFfS-o  |
|  Análisis Datos | Realiza análisis de datos de equipos y estudiantes del laboratorio de ingeniería electrónica.  | https://youtu.be/mU-Xq8a6jLY  |
|  Abrir Laboratorio | Realiza el proceso para abrir los laboratorios de electrónica.  | https://youtu.be/JkvYN6L3R9c  |
| Solicitar equipo  | Realiza el proceso para solicitar un equipo del laboratorio de ingeniería electrónica que un estudiante haya solicitado previamente.  | https://youtu.be/QuwEV_A2CnY  |
|  Solicitar historial | Realiza el proceso para solicitar las bases de datos requeridas del sistema mediante un correo electrónico.  | https://youtu.be/-3OULiFHrfc  |
| Registro control laboratorio  | Realiza el proceso para registrar personal al control de laboratorios de ingeniería electrónica.  | https://youtu.be/53JDDIMMXrE  |
|  Registro equipo | Realiza el proceso para registrar un equipo del laboratorio de ingeniería electrónica.  | https://youtu.be/ePIe5yH3uiE  |
|Registro monitor   | Realiza el proceso para registrar un monitor del laboratorio de ingeniería electrónica.  |  https://youtu.be/3gVNZVkuPmk |
|  Registro estudiante | Realiza el proceso para registrar un estudiante de ingeniería electrónica en el sistema.  |  https://youtu.be/cpcdLc9PSZc |
|  Registro base de datos estudiantes | Realiza el proceso para actualizar la base de datos de los estudiantes de ingeniería electrónica.  | https://youtu.be/elBU-qL3yUw  |
|Eliminar equipo   | Realiza el proceso para eliminar un equipo del sistema FastPEL del laboratorio de ingeniería electrónica.  | https://youtu.be/ogdPXvS2zpw  |
| Eliminar monitor  | Realiza el proceso para eliminar un monitor del laboratorio de ingeniería electrónica.  | https://youtu.be/HIZtb7nsmN0  |
| Eliminar estudiante  | Realiza el proceso para eliminar un estudiante del sistema de FastPEL del laboratorio de ingeniería electrónica.  | https://youtu.be/W6eZYUZoJbQ  |
| Eliminar estudiante control laboratorio  | Realiza el proceso para eliminar personal del control de laboratorios de ingeniería electrónica.  | https://youtu.be/K203fOP9MGo  |
|  Nuevo post | Realiza el proceso para crear, modificar y eliminar publicaciones informativas en el sistema de FastPEL del laboratorio de ingeniería electrónica.  | https://youtu.be/4JILY3WcZ_I  |



## *Importante*
Para el correcto funcionamiento del software, hay que tener en cuenta los siguientes puntos:
- Las bases de datos son archivos .csv.
- No se puede modificar los nombres de las bases de datos.
- No se puede modificar las cabeceras de las bases de datos.
- Las bases de datos tienen que estar en una carpeta llamada "data" alojada en la raíz del proyecto junto a "src".
- La raíz del proyecto en el servidor se encuentra alojado en la siguiente ruta: /home/usuario/gitlab_repos/fastpel/
- El usuario del administrador siempre tendrá que tener como nombre de usuario "Administrador".
- Solo existe un usuario para los monitores el cual siempre tendrá que tener como nombre de usuario "Monitores".
- Es preferible no utilizar caracteres como la ñ o vocales con tildes en el sistema.

## Soluciones a posibles inconvenientes

**¿El sistema de FastPEL se encuentra caído o no carga?**

Es posible que su computador se haya desconectado del Wifi correspondiente, de no ser así, puede que el servidor de FastPEL se haya caído, lo cual se debe reiniciar el servidor mediante ssh e iniciar nuevamente el sistema como se mencionó anteriormente.

**¿El sistema de control de acceso no funciona?**

Para solucionar diversos errores de funcionamiento del sistema de control de acceso, se debe reiniciar el control de acceso, esto lo podemos lograr conectándonos mediante ssh a la raspberry pi y reiniciándola o podemos ingresar a la caja metálica que se encuentra dentro del laboratorio y se apaga y se vuelve a encender el interruptor del cable de alimentación de la raspberry, luego de unos minutos el sistema debe funcionar correctamente, en el peor de los casos, desconecte y conecte el cable de alimentación de todo el sistema, esto hará que se apague la raspberry pi y los circuitos, reiniciando así todo el sistema.

¿No se solucionó el problema?

Es posible que el Wifi Ai_lab este caído o sin acceso a internet por lo que la raspberry no se puede comunicar con el servidor de FastPEL por lo que hay solucionar que el wifi funcione correctamente, por otro lado, si el wifi funciona correctamente y ya se reinició el sistema del control de acceso, es posible que el servidor de FastPEL se encuentre caído (no la raspberry pi), por lo cual se debe reiniciar el servidor de FastPEL mediante ssh e iniciar nuevamente el sistema como se mencionó anteriormente.

**¿Al realizar un préstamo, el sistema informa que el equipo no existe?**

Verificar si se está digitando bien el código en el campo correspondiente, usualmente la pistola lectora de códigos de barra, falla a la hora de escanear los códigos de barras de los equipos debido a que estos son reflectantes.

¿No se solucionó el problema?

Ir al final de la página de registral equipo y buscar el equipo que tiene incidente en la tabla de los equipos, puede buscarlo por el activo nuevo o el nombre, simplemente oprime "CTRL+f" y escribe el código del equipo o el nombre, si lo encuentras y esta correcto su activo nuevo, probablemente se está digitando mal el código en el préstamo, si no se encuentra dicho equipo, procede a realizar su correspondiente registro.

**¿Al realizar un préstamo, el sistema informa que el estudiante no existe?**

Verificar si se está digitando bien el código en el campo correspondiente, usualmente la pistola lectora de códigos de barra, falla a la hora de escanear los códigos de barras.

¿No se solucionó el problema?

Ir al final de la página de registrar estudiante y buscar el estudiante que tiene incidente en la tabla de los estudiantes, puede buscarlo por el código o el nombre, simplemente oprime "CTRL+f" y escribe el código del estudiante o el nombre, si lo encuentras y esta correcto su información, probablemente se está digitando mal el código en el préstamo, si no se encuentra dicho estudiante, procede a realizar su correspondiente registro.

***
## Autores
#### Universidad de Ibagué
#### Programa de Electrónica
#### Proyecto de Grado

- [Bryan F. Fandiño] - (bryanfely@gmail.com)
- [Harold F MURCIA] - Tutor

***
[Harold F MURCIA]: <http://haroldmurcia.com>

# FASTPEL

Un software con login e interfaz en html que permite realizar prestamos de equipos en el laboratorio de ingenieria electronica en la Universidad de Ibagué por medio de codigos de barras, tambien brinda asistencia para solicitar un laboratorio en horas extras.

Los contenidos de este repositorio:
  - Codigos fuentes
  - Scripts de desarrollo Python
  - Base de datos

## Elementos de hardware
  - Pistola lectora de codigos de barras

## Requisitos de Software
  - Ubuntu
  - Python 2.7 
  - Bases de datos
  
### Como se instalar el software
Para el correcto funcionamiento, es necesario realizar unos pasos previos antes de iniciar la aplicacion (esto solo se realizara una unica vez):

-Instalar multiles librerias (esto se realizara una unica vez):
```sh
Flask
flask_sqlalchemy
flask-bcrypt
Flask-Mail
flask-login
pil
request
flashplugin
pandas
iPython
Flask-WTF
WTForms
itsdangerous
```
Se instala con la siguiente linea usando *pip*
```sh
pip install "nombre de la libreria"
```
-Poner el correo electronico (gmail) y contraseña del administrador ya que es necesario para el correcto funcionamiento de algunas funciones, su contraseña sera encriptada y no se hara manejo del correo sin su autorizacion, por ende no se tiene que preocupar.
Para hacer esta configuracion, entre a la carpeta flaskblog luego, abra el archivo "__ init__.py" y cambie las variables (sin quitar las comillas):
```sh
'correo_del_administrador'
'contraseña_del_correo_del_administrador' 
```
Guarde y salga, (esto se realizara una unica vez).

-Da permisos a tu cuenta de gmail que pusiste en el "correo_del_administrador", para esto abre tu cuenta gmail y ve a "administra tu cuenta de google" luego le das en "Seguridad" despues vas en "Acceso de apps menos seguras" le das en "Activar el acceso" por ultimo le das si a "Permitir el acceso de apps menos seguras" (esto se realizara una unica vez)

-Luego tiene que poner su IP, para ello entra al archivo "run .py" y donde dice 
```sh 
host='su_IP' 
```
cambia su_IP por tu IP (sin quitar las comillas, esto se realizara una unica vez).

-Continiamos creando nuesta base de datos de usuarios, para esto abrimos la terminal y vamos a la carpeta donde esta el archivo "run .py", habrimos python y desde ahi y ejecutamos las siguintes lineas (esto se realizara una unica vez):

```sh 
from flaskblog import db
db.create_all()
```
cerramos python con:
```sh 
exit()
```	
-Finalmente se debe crear dos cuentas en Fastpel, una del administrador y otra de los monitores para esto corremos el software y vamos a "Registrate", ponemos Administrador como nombre (obligatorio) luego ingresa un email y una contraseña (no es la contraseña del email, es una nueva contraseña para la cuenta de software); para monitores hacemos lo mismos pasos anteriores con la diferencia de que el nombre sera Monitores (obligatorio, esto se realizara una unica vez)

-El software ya esta configurado completamente.

### Como se corre el software
Para correr nuestro software abrimos la terminal y vamos a la carpeta donde esta el archivo "run .py" y ejecutamos la siguiente linea (esto se realizara cada vez que se corra el software).:
```sh 
sudo python run.py
```	
### Funciones de FastPEL
- Registro de usuario nuevo
- Restablecer la contraceña de un usuario
- Modificar datos de un usuario
- Postear informacion para los usuarios (administador y monitores)
- Modificar o eliminar post (administador y monitores)
- Prestamo  (administador y monitores)
- Devolucion (administador y monitores)
- Solicitar equipo (administador y monitores)
- Laboratorios
###  Prestamo
En la opcion de *Prestamo* se solicita el codigo de barras del carnet del estudiante y del equipo a solicitar luego, el software busca la informacion de estos codigos en la base de datos de los estudiantes y de los equipos de laboratorio respectivamente:
```sh
datos_estudiantes = pd.read_csv('Estudiantes v2.csv')
self.alumno = datos_estudiantes.loc[(datos_estudiantes)['CODIGO'] == codigo]
    
datos_equipos = pd.read_csv('Base equipos v2.csv')
self.equipo = datos_equipos.loc[(datos_equipos)['ACTIVO NUEVO'] == codigo]
```
Finalmente se guarda la informacion del prestamo en una base de datos de los prestamos actuales y otra con el historial de prestamos:
```sh
informacion_con_estado.reset_index(drop = True).to_csv('Historial v2.csv',header=False, index=False, mode='a')

informacion_sin_fecha.reset_index(drop = True).to_csv('Prestamos v2.csv',header=False, index=False, mode='a')
```

###  Devolucion
En la opcion de *Devolucion* se solicita el codigo de barras del equipo a devolver luego, el software busca la informacion del codigo en la base de datos de los prestamos actuales:
```sh
datos_prestamos=pd.read_csv('Prestamos v2.csv')
equipo_en_prestamo=datos_prestamos.loc[(datos_prestamos)['ACTIVO NUEVO']==equipo]
```
Finalmente se elimina la informacion del registro en la base de datos de los prestamos actuales y en la base de de datos del historial queda regisdtrada la entrega del equipo:
```sh
informacion_con_estado.reset_index(drop = True).to_csv('Historial v2.csv',header=False, index=False, mode='a')
```

###  Solicitar equipo
En la opcion de *Solicitar equipo* se solicita el codigo de barras del equipo a solicitar y automaticamente el software busca la informacion necesaria de la persona en la base de datos de prestamos v2 para enviar un correo electronico, finalmente el software redacta y envia el correo electronico:
```sh
destinatario = direc_correo.item()
msg = Message('Devolucion urgente del equipo de laboratorio',
sender='noreply@demo.com',
recipients=[destinatario])

eq=equipo_prestado['EQUIPO']
eq = eq.item()
msg.body = "Cordial saludo estimado alumno, se le solicita la DEVOLUCION INMEDIATA del equipo "+ str(eq)+ " codigo: "+ str(codg) +"."
mail.send(msg)
```

###  Laboratorios
En la opcion de *Laboratorios* trata de facilitar la solicitud de laboratorios en horario extra, el estudiante tiene que registrarse e ingresar al software, seleccionar un laboratorio de tres que se pueden solicitar, luego tiene que llenar un formulario con la información necesaria, esta información queda guardada en una bases de datos y se muestra los estudiantes registrados en una tabla para saber el cupo disponible, pero si el laboratorio ya está con el cupo lleno, el estudiante puede registrase en otro laboratorio, si se alcanza el cupo limite del respectivo laboratorio, el software automáticamente envía un correo electrónico a la primera persona que se registró con toda la información de los estudiantes registrados, estos registros deben hacerse en los horarios establecidos (6am - 11 am), luego de esta hora, los registros no se podrán realizar debido que el software cierra esta opción y la base de datos creada se reinicia cada día.

###  NUEVO POST
Esta opción sirve para informar a estudiantes de avisos o eventos de los laboratorios mediante posts generados por el administrador o monitores, estos posts se pueden editar o eliminar en su defecto. 

###  RESTABLECER CONTRASEÑA
 El software consta de esta la opción restablecer una contraseña de un usuario, mediante el envío de un correo electrónico el cual tiene un link para restablecer la contraseña.
 
###  CUENTA
 El usuario tiene la opción de modificar el email y contraseña (las cuales están cifradas para una mayor seguridad) como también una foto asignada por defecto a los usuarios.

Aqui podras ver un [Video tutorial] del software 

## *Importante*
Para el correcto funcionamineto del software, hay que tener en cuenta los siguientes puntos:
- Las bases de datos son archivos .csv.
- No se puede modificar los nombres de las bases de datos.
- No se puede modificar las cabeceras de las bases de datos.
- Las bases de datos tienen que estar en una carpeta llamada bases de datos.
- EL contenido de la carpeta src tiene que ir en una carpeta llamada web y creada en la misma direccion que la carpeta base de datos.
- No se pueden utilizar caracteres como la ñ o vocales con tildes.

***

### Autolaunch
cd .... repositorio
bash config.sh


## Autores
#### Universidad de Ibagué
#### Programa de Electrónica
#### Electrónica Digial III 2019B

- [Bryan F. Fandiño] - (2420162019@estudiantesunibague.edu.co)
- [Harold F MURCIA] - Tutor

***
[Video tutorial]: <https://youtu.be/vdMDUCXMcxs>
[Harold F MURCIA]: <http://haroldmurcia.com>

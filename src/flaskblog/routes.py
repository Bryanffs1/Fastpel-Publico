#!/user/bin/env python
# -*- coding: utf-8 -*-

import os
import secrets
from PIL import Image
from flask import render_template, request, url_for, redirect, flash, abort
from numpy import append
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

import pandas as pd
from IPython.display import HTML
import time
from datetime import datetime # hora
from os import remove
import socket
from key_generator.key_generator import generate

@app.route('/')
@app.route('/Fastpel')
def Fastpel():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template("Fastpel.html", posts=posts, segment='Fastpel')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('Fastpel'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Tu cuenta ha sido creada! Ahora puede iniciar sesion','success') # flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form, segment='register')

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('Fastpel'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('Fastpel'))
        else:
            flash('Inicio de sesion fallido, verifique el correo electronico y el password','danger') # flash(f'Account created for {form.username.data}!', 'success')
    return render_template("login.html", title='Inicio de sesion', form=form, segment='login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('Fastpel'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # random_hex = str(os.urandom(8))
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Su cuenta ha sido actualizada!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Cuenta', image_file=image_file, form=form, segment='account')

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Tu publicacion ha sido creada!', 'success')
        return redirect(url_for('Fastpel'))
    return render_template('create_post.html', title='Nueva publicacion', form=form, legend='Nueva publicacion', segment='new_post')

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Tu publicacion ha sido actualizada!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Actualizar publicacion', form=form, legend='Actualizar publicacion')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Tu publicacion ha sido eliminada!', 'success')
    return redirect(url_for('Fastpel'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Solicitud de restablecimiento de password',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = '''Para restablecer su password, visite el siguiente enlace:
'{}',
Si no realizo esta solicitud, simplemente ignore este correo electronico y no se realizaran cambios.'''.format(url_for('reset_token', token=token, _external=True))
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('Fastpel'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Se ha enviado un correo electronico con instrucciones para restablecer su password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Restablecer el Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('Fastpel'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Ese es un token no valido o caducado', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Su password ha sido actualizada! Ahora puede iniciar sesion', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Restablecer el Password', form=form)

###########################################################################
#                   OPCIONES FASTPEL
###########################################################################
@app.route('/Prestamos', methods=['GET','POST'])
@login_required
def Prestamos():
    
    if request.method == 'POST':
        id = int(request.form.get('did'))           # codigo verificacion de monitores
        leer_verificacion= pd.read_csv('../data/Monitores_id.csv')
        leer_id_verificacion = leer_verificacion['ID'].tolist()
        verificacion_moni = id in leer_id_verificacion

        # for x in range(5):
        #     print("bryan" + str(x))
        cequi = int(request.form.get('cequi'))
        cequi = cequi + 1
        for x in range(1,cequi):

            if verificacion_moni is True:
                eq = str(request.form.get('cequipo'+ str(x)))            # VERIFICAR SI NO ESTA PRESTADO EL EQUIPO
                datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                vequipo=datos_prestamos['ACTIVO NUEVO'].tolist()
                verificacion_equi_prest = eq in vequipo

                if verificacion_equi_prest is False:
                    cestudiante = int(request.form.get('cestudiante'))         # VERIFICAR SI EL ALUMNO EXISTE
                    datos_estudiantes = pd.read_csv('../data/Estudiantes v2.csv')
                    valumno=datos_estudiantes['CODIGO'].tolist()
                    verificacion_estu_existe = cestudiante in valumno

                    if verificacion_estu_existe is True:
                        datos_equipos = pd.read_csv('../data/Base equipos v2.csv') # VERIFICAR SI EL EQUIPO EXISTE
                        vqq=datos_equipos['ACTIVO NUEVO'].tolist()
                        verificacion_equi_exis = eq in vqq

                        if verificacion_equi_exis is True:
                            alumno = datos_estudiantes.loc[(datos_estudiantes)['CODIGO'] == cestudiante]
                            equipo = datos_equipos.loc[(datos_equipos)['ACTIVO NUEVO'] == eq]

                            fecha = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
                            espacio = pd.DataFrame({'':['']})
                            estado = pd.DataFrame({'FECHA':[fecha]})
                            fecha_prestamo = pd.DataFrame({'FECHA':[fecha]})
                            estadoo = pd.DataFrame({'':[''],'ESTADO':['Prestado']})

                            inf_monitor = leer_verificacion.loc[(leer_verificacion)['ID'] == id]
                            nom_monitor = inf_monitor['NOMBRE']
                            nom_monitor = nom_monitor.item()
                            n_monitor = pd.DataFrame({'':[''],'MONITOR':[nom_monitor]})

                            informacion = pd.merge(alumno, equipo, on="ja", how="outer")
                            informacion_con_estado = pd.concat([informacion, estadoo, estado, espacio, espacio, n_monitor], axis=1)
                            informacion_con_fecha = pd.concat([informacion, estadoo,fecha_prestamo], axis=1)

                            print("entrada " + str(eq))
                            print (informacion_con_fecha)

                            try:
                                print('')
                                # print ("\t", alumno.iloc[0,0],'saco:',equipo.iloc[0,4])

                                informacion_con_estado.reset_index(drop = True).to_csv('../data/Historial v2.csv',header=False, index=False, mode='a')
                                informacion_con_fecha.reset_index(drop = True).to_csv('../data/Prestamos v2.csv',header=False, index=False, mode='a')
                                
                                datos_duplicados = pd.read_csv('../data/Prestamos v2.csv')
                                datos_duplicados=datos_duplicados.drop_duplicates(subset=['ACTIVO NUEVO'])
                                datos_duplicados.reset_index(drop = True).to_csv('../data/Prestamos v2.csv',header=True, index=False)
                                datos_duplicados.reset_index(drop = True).to_csv('../data/Prestamos v2.csv',header=True, index=False)

                                flash('El equipo' + str(x) +' se registro satisfactoriamente', 'success') # info  success warning
                                # info= alumno.iloc[0,1] + '   saco:   ' + equipo.iloc[0,4]  #"Registro guardado"
                                print("\n Registro del equipo" + str(x) + " guardado\n")

                            except:
                                flash('Datos mal ingresados, por favor intente de nuevo', 'warning') # info  success warning
                                info= "ERROR: Datos mal ingresados, por favor intente de nuevo"
                                print ("\n\n!!!!!ERROR: datos mal ingresados")
                                print ("por favor intente de nuevo!!!")

                                datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                                df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
                                tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

                                return render_template("prestamo.html", info=info, title='Prestamos', tabla_prestamos=tabla_prestamos, segment='Prestamos')

                        if verificacion_equi_exis is False:
                            flash('El equipo' + str(x) +' ingresado no existe, por favor intenta de nuevo', 'warning') # info  success warning
                            # info= "ERROR: El equipo" + str(x) +" ingresado no existe, por favor intenta de nuevo"
                            print ("\n\n!!!!!ERROR: El equipo no existe, por favor intenta de nuevo")
                            # return render_template("prestamo.html", info=info, title='Prestamos', segment='Prestamos')

                    if verificacion_estu_existe is False:
                        flash('El alumno ingresado no existe, por favor intenta de nuevo', 'warning') # info  success warning
                        info= "ERROR: El alumno ingresado no existe, por favor intenta de nuevo"
                        print ("\n\n!!!!!ERROR: El alumno no existe, por favor intenta de nuevo")

                        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                        df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
                        tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

                        return render_template("prestamo.html", info=info, title='Prestamos',tabla_prestamos=tabla_prestamos, segment='Prestamos')

                if verificacion_equi_prest is True:
                    flash('El equipo' + str(x) +' ya esta prestado, por favor intenta de nuevo', 'warning') # info  success warning
                    # info= "ERROR: El equipo" + str(x) +" ya esta prestado, por favor intenta de nuevo"
                    print ("\n\n!!!!!ERROR: El equipo ya esta prestado, por favor intenta de nuevo")
                    # return render_template("prestamo.html", info=info, title='Prestamos', segment='Prestamos')

            if verificacion_moni is False:
                flash('Prestamo Fallido, contraseña del monitor no válida, por favor intenta de nuevo', 'warning')
                info = "ERROR: Prestamo Fallido, contraseña del monitor no válida, por favor intenta de nuevo"

                datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
                tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

                return render_template("prestamo.html", info=info, title='Prestamos', tabla_prestamos=tabla_prestamos, segment='Prestamos')

        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
        df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
        tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

        return render_template("prestamo.html", title='Prestamos', tabla_prestamos=tabla_prestamos, segment='Prestamos')

    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    return render_template("prestamo.html", title='Prestamos', tabla_prestamos=tabla_prestamos, segment='Prestamos')
    # return redirect(url_for('ruta'))


@app.route('/Devoluciones', methods=['GET','POST'])
@login_required
def Devoluciones():

    if request.method == 'POST':
        id2 = int(request.form.get('did2'))         # codigo new verificacion2 de monitores
        leer_verificacion2= pd.read_csv('../data/Monitores_id.csv')
        leer_id_verificacion2 = leer_verificacion2['ID'].tolist()
        verificacion2 = id2 in leer_id_verificacion2

        if verificacion2 is True:

            eq = str(request.form.get('ceqdeb'))            # VERIFICAR SI ESTA PRESTADO EL EQUIPO
            datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
            vvequipo=datos_prestamos['ACTIVO NUEVO'].tolist()
            verificacion_equi_prest = eq in vvequipo

            if verificacion_equi_prest is True:

                eqd = str(request.form.get('ceqdeb'))
                equipo_en_prestamo=datos_prestamos.loc[(datos_prestamos)['ACTIVO NUEVO'] == eqd]

                obss = str(request.form.get('obser')) #.decode('utf-8')
                observacion=pd.DataFrame({'':[''],'OBSERVACION':[obss]})

                inf_monitor = leer_verificacion2.loc[(leer_verificacion2)['ID'] == id2] #poner nombre del monitor actual
                nom_monitor = inf_monitor['NOMBRE']
                nom_monitor = nom_monitor.item()
                print ('\n\t Monitor: ', nom_monitor)
                n_monitor = pd.DataFrame({'':[''],'MONITOR':[nom_monitor]})

                fecha = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())

                informacion_cambio_estado=equipo_en_prestamo.replace({'ESTADO': "Prestado"}, "Entregado")
                informacion_cambio_estado_fecha=informacion_cambio_estado.replace({'FECHA': equipo_en_prestamo['FECHA'].item()}, fecha)
                informacion_cambio_estado_fecha.reset_index(inplace = True)   #para poner el index en 0 para contatenar bien con el estado
                informacion_cambio_estado_bueno=informacion_cambio_estado_fecha.drop(['index'], axis=1)   #para eliminar index antiguo

                informacion_con_estado_y_observacion = pd.concat([informacion_cambio_estado_bueno, observacion, n_monitor], axis=1,)

                sacar=datos_prestamos.loc[(datos_prestamos)['ACTIVO NUEVO']!=eqd]
                print ("\t", informacion_cambio_estado_bueno.iloc[0,1],'tiene:',informacion_cambio_estado_bueno.iloc[0,8])

                informacion_con_estado_y_observacion.reset_index(drop = True).to_csv('../data/Historial v2.csv',header=False, index=False, mode='a')
                sacar.reset_index(drop = True).to_csv('../data/Prestamos v2.csv',header=True, index=False)
                print ("\t", informacion_cambio_estado_bueno.iloc[0,1],'entrego:',informacion_cambio_estado_bueno.iloc[0,8])

                codigo_est_sacar_sn = equipo_en_prestamo.loc[:,'CODIGO'].item()
                datos_prestamos_sn=pd.read_csv('../data/Prestamos v2.csv')
                dato_est_sacar_sn =len(datos_prestamos_sn.loc[(datos_prestamos_sn)['CODIGO'] == codigo_est_sacar_sn])
                
                equ_al_sn = datos_prestamos_sn.loc[(datos_prestamos_sn)['CODIGO'] == codigo_est_sacar_sn]
                equ_al_sn = equ_al_sn[['ACTIVO NUEVO']]
                list_equ_al_sn =[]
                for i in range(dato_est_sacar_sn):
                    list_equ_al_sn.append(equ_al_sn.iloc[i].item())
                list_equ_al_sn = str(list_equ_al_sn)[1:-1]

                print(f"\t {equipo_en_prestamo.loc[:,'NOMBRE'].item()} debe {dato_est_sacar_sn} equipos: {list_equ_al_sn}\n")
                flash('Devolucion realizada', 'success')
                info = str(informacion_cambio_estado_bueno.iloc[0,1]) + '    entrego:    ' + str(informacion_cambio_estado_bueno.iloc[0,8])
                info2 = str(f"{equipo_en_prestamo.loc[:,'NOMBRE'].item()} debe {dato_est_sacar_sn} equipos: {list_equ_al_sn}")

                datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
                tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

                return render_template("devolucion.html", info=info, info2=info2, title='Devoluciones', tabla_prestamos=tabla_prestamos, segment='Devoluciones')

            if verificacion_equi_prest is False:
                flash('Codigo mal ingresado o el equipo no esta en prestamo', 'warning') # info  success warning
                info= "ERROR: Codigo mal ingresado o el equipo no esta en prestamo"
                print ("\nERROR: Codigo mal ingresado o el equipo no esta en prestamo\n")

                datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
                df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
                tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

                return render_template("devolucion.html", info=info, title='Devoluciones', tabla_prestamos=tabla_prestamos, segment='Devoluciones')

        if verificacion2 is False:
            flash('Prestamo Fallido, contraseña del monitor no válida, por favor intenta de nuevo', 'warning')
            info = "ERROR: Prestamo Fallido, contraseña del monitor no válida, por favor intenta de nuevo"

            datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
            df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
            tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

            return render_template("devolucion.html", info=info, title='Devoluciones', tabla_prestamos=tabla_prestamos, segment='Devoluciones')

    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    return render_template("devolucion.html", title='Devoluciones', tabla_prestamos=tabla_prestamos, segment='Devoluciones')


@app.route('/AnalisisDatos', methods=['GET','POST'])
@login_required
def AnalisisDatos():

    datos_Ahistorial=pd.read_csv('../data/Historial v2.csv', parse_dates=['FECHA'], date_parser=lambda x: pd.to_datetime(x, format='%d/%m/%Y %H:%M:%S')) #lo demas es para darle el formato correcto a la fecha
    datos_Aprestamos=pd.read_csv('../data/Prestamos v2.csv')

    Dataframe_equipo_m_prestado = pd.DataFrame({'EQUIPO': [], 'ACTIVO NUEVO': [],'VECES PRESTADO': []},columns=['EQUIPO', 'ACTIVO NUEVO','VECES PRESTADO'])
    codigoo_equipos = []
    for i in datos_Ahistorial["ACTIVO NUEVO"]:
        if i not in codigoo_equipos:
            codigoo_equipos.append(i)
    for k in range(0,len(codigoo_equipos)):
        N_equipos = datos_Ahistorial[datos_Ahistorial["ACTIVO NUEVO"]==codigoo_equipos[k]]
        veces_prestado = len(N_equipos)/2
        Dataframe_equipo_m_prestado.at[k+1,"EQUIPO"] = N_equipos.iloc[0,8]
        Dataframe_equipo_m_prestado.at[k+1,"ACTIVO NUEVO"] = codigoo_equipos[k]
        Dataframe_equipo_m_prestado.at[k+1,"VECES PRESTADO"] = veces_prestado

    Dataframe_equipo_m_prestadoo = Dataframe_equipo_m_prestado.sort_values(by = "VECES PRESTADO",  ascending=False)
    Dataframe_equipo_m_prestadoo = Dataframe_equipo_m_prestadoo.drop_duplicates(subset=['ACTIVO NUEVO'], ignore_index=True)
    equipos_max_unidos = Dataframe_equipo_m_prestadoo[:10]

    equipos_max_pres = equipos_max_unidos[['EQUIPO','ACTIVO NUEVO','VECES PRESTADO']]
    tabla_eq_mas_prestado = HTML(equipos_max_pres.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    equipo_menos_prestado = Dataframe_equipo_m_prestado[Dataframe_equipo_m_prestado["VECES PRESTADO"]==Dataframe_equipo_m_prestado["VECES PRESTADO"].min()]
    eq_menos_pres = equipo_menos_prestado[['EQUIPO','ACTIVO NUEVO','VECES PRESTADO']]
    tabla_eq_menos_prestado = HTML(eq_menos_pres.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    Dataframe_estudiante_m_prestado = pd.DataFrame({'CODIGO': [],'NOMBRE': [], 'SOLICITUDES': []},columns=['CODIGO', 'NOMBRE', 'SOLICITUDES'])
    cod_estudiante = []
    for p in datos_Ahistorial["CODIGO"]:
        if p not in cod_estudiante:
            cod_estudiante.append(p)
    for q in range(0,len(cod_estudiante)):
        N_solicitudes = datos_Ahistorial[datos_Ahistorial["CODIGO"]==cod_estudiante[q]]
        V_solicitudes = (len(N_solicitudes))/2
        Dataframe_estudiante_m_prestado.at[q+1,"CODIGO"] = str(cod_estudiante[q])
        Dataframe_estudiante_m_prestado.at[q+1,"NOMBRE"] = N_solicitudes.iloc[0,1]
        Dataframe_estudiante_m_prestado.at[q+1,"SOLICITUDES"] = V_solicitudes

    Dataframe_estudiante_m_prestadoo = Dataframe_estudiante_m_prestado.sort_values(by = "SOLICITUDES",  ascending=False)
    Dataframe_estudiante_m_prestadoo = Dataframe_estudiante_m_prestadoo.drop_duplicates(subset=['CODIGO'], ignore_index=True)
    estudiantes_max_prestado = Dataframe_estudiante_m_prestadoo[:10]

    es_max_pres = estudiantes_max_prestado[['CODIGO','NOMBRE','SOLICITUDES']]
    tabla_es_mas_prestado = HTML(es_max_pres.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    datos_Ahistorial['FECHA'] = pd.to_datetime(datos_Ahistorial['FECHA']).dt.date # poner formato de fecha y quitar hora

    try:
        fechamin_historial = min(datos_Ahistorial['FECHA'])
    except:
        fechamin_historial = str("NN")

    Prest_fin_total = round((len(datos_Ahistorial)-len(datos_Aprestamos))/2)

    datos_prestamos_actual=pd.read_csv('../data/Prestamos v2.csv')
    datos_prestamos_actual = len(datos_prestamos_actual)

    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    if request.method == 'POST':
        cod_equipo = str(request.form.get('codequihtml'))
        equipo_en_prestamo=Dataframe_equipo_m_prestado.loc[(Dataframe_equipo_m_prestado)['ACTIVO NUEVO'] == cod_equipo]

        if cod_equipo in Dataframe_equipo_m_prestado['ACTIVO NUEVO'].tolist():
            flash('Busqueda realizada', 'success')
            info = 'El equipo '+ str(equipo_en_prestamo.iloc[0,0]) + ' codigo: ' + str(equipo_en_prestamo.iloc[0,1]) + ' se ha prestado: ' + str(int(equipo_en_prestamo.iloc[0,2]))+' veces desde el '+ str(fechamin_historial )

            return render_template("AnalisisDatos.html", title='AnalisisDatos',
            info=info, Prest_fin_total=Prest_fin_total, fechamin_historial=fechamin_historial, datos_prestamos_actual=datos_prestamos_actual,
            tabla_eq_menos_prestado=tabla_eq_menos_prestado, tabla_eq_mas_prestado=tabla_eq_mas_prestado,
            tabla_es_mas_prestado=tabla_es_mas_prestado, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

        if cod_equipo not in Dataframe_equipo_m_prestado['ACTIVO NUEVO'].tolist():
            flash('Busqueda realizada', 'success')
            info = 'El equipo '+ str(cod_equipo) + ' nunca se ha prestado desde el '+ str(fechamin_historial )

        cod_estuhtml = str(request.form.get('codestuhtml'))
        estudiante_solicitudes = Dataframe_estudiante_m_prestado.loc[(Dataframe_estudiante_m_prestado)['CODIGO'] == cod_estuhtml]
        if cod_estuhtml in Dataframe_estudiante_m_prestado['CODIGO'].tolist():
            flash('Busqueda realizada', 'success')
            info2 = 'El estudiante '+ str(estudiante_solicitudes.iloc[0,1]) + ' codigo: '+str(estudiante_solicitudes.iloc[0,0])+' ha realizado: ' + str(int(estudiante_solicitudes.iloc[0,2]))+' solicitudes de equipos desde el '+ str(fechamin_historial )

            return render_template("AnalisisDatos.html", title='AnalisisDatos',
            info2=info2, Prest_fin_total=Prest_fin_total, fechamin_historial=fechamin_historial, datos_prestamos_actual=datos_prestamos_actual,
            tabla_eq_menos_prestado=tabla_eq_menos_prestado, tabla_eq_mas_prestado=tabla_eq_mas_prestado,
            tabla_es_mas_prestado=tabla_es_mas_prestado, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

        if cod_estuhtml not in Dataframe_estudiante_m_prestado['CODIGO'].tolist():
            flash('Busqueda realizada', 'success')
            info2 = 'El estudiante '+ str(cod_estuhtml) + ' nunca ha realizado solicitudes desde el '+ str(fechamin_historial )

        return render_template("AnalisisDatos.html", title='AnalisisDatos',
        info=info, info2=info2, Prest_fin_total=Prest_fin_total, fechamin_historial=fechamin_historial, datos_prestamos_actual=datos_prestamos_actual,
        tabla_eq_menos_prestado=tabla_eq_menos_prestado, tabla_eq_mas_prestado=tabla_eq_mas_prestado,
        tabla_es_mas_prestado=tabla_es_mas_prestado, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

    return render_template("AnalisisDatos.html", title='AnalisisDatos',
    Prest_fin_total=Prest_fin_total, fechamin_historial=fechamin_historial, datos_prestamos_actual=datos_prestamos_actual,
    tabla_eq_menos_prestado=tabla_eq_menos_prestado, tabla_eq_mas_prestado=tabla_eq_mas_prestado,
    tabla_es_mas_prestado=tabla_es_mas_prestado, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

@app.route('/AnalisisDatosFecha', methods=['GET','POST'])
@login_required
def AnalisisDatosFecha():

    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    if request.method == 'POST':

        date_ini_equi = str(request.form.get('datequihtmlini'))#datetime.strptime(request.form.get('datequihtmlini'),'%Y-%m-%d')
        date_fin_equi = str(request.form.get('datequihtmlfin'))
        opciondatos = str(request.form.get('opciondatos'))

        datos_FFhistorial=pd.read_csv('../data/Historial v2.csv', parse_dates=['FECHA'], date_parser=lambda x: pd.to_datetime(x, format='%d/%m/%Y %H:%M:%S'))
        datos_FFhistorial['FECHA'] = pd.to_datetime(datos_FFhistorial['FECHA']).dt.date # poner formato de fecha y quitar hora

        date_ini_equid = pd.to_datetime(date_ini_equi).date()
        date_fin_equid = pd.to_datetime(date_fin_equi).date()
        datos_Fhistorial = datos_FFhistorial.loc[datos_FFhistorial["FECHA"].between(date_ini_equid, date_fin_equid)]

        Dataframe_equipo_m_prestado_fecha = pd.DataFrame({'EQUIPO': [], 'ACTIVO NUEVO': [],'VECES PRESTADO': []},columns=['EQUIPO', 'ACTIVO NUEVO','VECES PRESTADO'])
        codigooo_equipos = []
        for i in datos_Fhistorial["ACTIVO NUEVO"]:
            if i not in codigooo_equipos:
                codigooo_equipos.append(i)
        for k in range(0,len(codigooo_equipos)):
            N_equipos_F = datos_Fhistorial[datos_Fhistorial["ACTIVO NUEVO"]==codigooo_equipos[k]]
            veces_prestado_F = len(N_equipos_F)/2
            Dataframe_equipo_m_prestado_fecha.at[k+1,"EQUIPO"] = N_equipos_F.iloc[0,8]
            Dataframe_equipo_m_prestado_fecha.at[k+1,"ACTIVO NUEVO"] = codigooo_equipos[k]
            Dataframe_equipo_m_prestado_fecha.at[k+1,"VECES PRESTADO"] = veces_prestado_F

        Dataframe_equipo_m_prestado_fecha_orden = Dataframe_equipo_m_prestado_fecha.sort_values(by = "VECES PRESTADO",  ascending=False)
        Dataframe_equipo_m_prestado_fecha_orden = Dataframe_equipo_m_prestado_fecha_orden.drop_duplicates(subset=['ACTIVO NUEVO'], ignore_index=True)

        if opciondatos == '5':
            equipos_max_unidos_F = Dataframe_equipo_m_prestado_fecha_orden[:5]

        if opciondatos == '10':
            equipos_max_unidos_F = Dataframe_equipo_m_prestado_fecha_orden[:10]

        if opciondatos == '20':
            equipos_max_unidos_F = Dataframe_equipo_m_prestado_fecha_orden[:20]

        if opciondatos == 'Todos':
            equipos_max_unidos_F = Dataframe_equipo_m_prestado_fecha_orden[:]

        equipos_max_pres_F = equipos_max_unidos_F[['EQUIPO','ACTIVO NUEVO','VECES PRESTADO']]
        tabla_eq_mas_prestado_fecha = HTML(equipos_max_pres_F.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

        flash('Busqueda realizada', 'success')
        info = "Sus datos se encuentran en la tabla superior"

        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
        df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
        tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

        return render_template("AnalisisDatosFecha.html", title='AnalisisDatosFecha',
        info=info, tabla_eq_mas_prestado_fecha=tabla_eq_mas_prestado_fecha, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

    return render_template("AnalisisDatosFecha.html", title='AnalisisDatosFecha',
    tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

@app.route('/AnalisisDatosFecha_estudiante', methods=['GET','POST'])
@login_required
def AnalisisDatosFecha_estudiante():

    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

    if request.method == 'POST':

        date_ini_equi2 = str(request.form.get('datequihtmlini'))#datetime.strptime(request.form.get('datequihtmlini'),'%Y-%m-%d')
        date_fin_equi2 = str(request.form.get('datequihtmlfin'))
        opciondatos2 = str(request.form.get('opciondatos'))

        datos_FFhistorial2=pd.read_csv('../data/Historial v2.csv', parse_dates=['FECHA'], date_parser=lambda x: pd.to_datetime(x, format='%d/%m/%Y %H:%M:%S'))
        datos_FFhistorial2['FECHA'] = pd.to_datetime(datos_FFhistorial2['FECHA']).dt.date # poner formato de fecha y quitar hora

        date_ini_equid = pd.to_datetime(date_ini_equi2).date()
        date_fin_equid = pd.to_datetime(date_fin_equi2).date()
        datos_Fhistorial2 = datos_FFhistorial2.loc[datos_FFhistorial2["FECHA"].between(date_ini_equid, date_fin_equid)]
        print(date_ini_equid,date_fin_equid)
        Dataframe_estudiante_m_prestado2 = pd.DataFrame({'CODIGO': [],'NOMBRE': [], 'SOLICITUDES': []},columns=['CODIGO', 'NOMBRE', 'SOLICITUDES'])
        cod_estudiante2 = []
        for p in datos_Fhistorial2["CODIGO"]:
            if p not in cod_estudiante2:
                cod_estudiante2.append(p)
        for q in range(0,len(cod_estudiante2)):
            N_solicitudes = datos_Fhistorial2[datos_Fhistorial2["CODIGO"]==cod_estudiante2[q]]
            V_solicitudes = (len(N_solicitudes))/2
            Dataframe_estudiante_m_prestado2.at[q+1,"CODIGO"] = str(cod_estudiante2[q])
            Dataframe_estudiante_m_prestado2.at[q+1,"NOMBRE"] = N_solicitudes.iloc[0,1]
            Dataframe_estudiante_m_prestado2.at[q+1,"SOLICITUDES"] = V_solicitudes

        Dataframe_estudiantes_m_prestado_fecha_orden2 = Dataframe_estudiante_m_prestado2.sort_values(by = "SOLICITUDES",  ascending=False)
        Dataframe_estudiantes_m_prestado_fecha_orden2 = Dataframe_estudiantes_m_prestado_fecha_orden2.drop_duplicates(subset=['CODIGO'], ignore_index=True)

        if opciondatos2 == '5':
            estudiante_max_unidos_F = Dataframe_estudiantes_m_prestado_fecha_orden2[:5]

        if opciondatos2 == '10':
            estudiante_max_unidos_F = Dataframe_estudiantes_m_prestado_fecha_orden2[:10]

        if opciondatos2 == '20':
            estudiante_max_unidos_F = Dataframe_estudiantes_m_prestado_fecha_orden2[:20]

        if opciondatos2 == 'Todos':
            estudiante_max_unidos_F = Dataframe_estudiantes_m_prestado_fecha_orden2[:]

        estud_max_pres_F2 = estudiante_max_unidos_F[['CODIGO','NOMBRE','SOLICITUDES']]
        tabla_estu_mas_prestado_fecha = HTML(estud_max_pres_F2.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

        flash('Busqueda realizada', 'success')
        info = "Sus datos se encuentran en la tabla superior"

        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
        df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
        tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))

        return render_template("AnalisisDatosFecha_estudiante.html", title='AnalisisDatosFecha_estudiante',
        info=info, tabla_estu_mas_prestado_fecha=tabla_estu_mas_prestado_fecha, tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

    return render_template("AnalisisDatosFecha_estudiante.html", title='AnalisisDatosFecha_estudiante',
    tabla_prestamos=tabla_prestamos, segment='AnalisisDatos')

@app.route('/Solicitar_equipo', methods=['GET','POST'])
@login_required
def Solicitar_equipo():
    # U15200501283
    if request.method == 'POST':
        print ("\n\n\t\t********************************\n") #encabezado
        print ("\t\t*    Enviar email con Gmail    *\n")
        print ("\t\t********************************\n")

        codg=str(request.form.get('ccequipo'))
        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
        equipo_prestado=datos_prestamos.loc[(datos_prestamos)['ACTIVO NUEVO']==codg]
        direc_correo = equipo_prestado['CORREO']
        try:
            print(equipo_prestado.iloc[0,4])  #      genera error si no existe el codigo, si no esta prestado el equipo
            destinatario = direc_correo.item()
            msg = Message('Devolucion urgente del equipo de laboratorio',
                          sender='noreply@demo.com',
                          recipients=[destinatario])

            eq=equipo_prestado['EQUIPO']
            eq = eq.item()
            msg.body = "Cordial saludo estimado alumno, se le solicita la DEVOLUCION INMEDIATA del equipo "+ str(eq)+ " codigo: "+ str(codg) +"."
            mail.send(msg)

            flash('Correo enviado', 'success')
            info="Correo enviado"
            print("\n-------Correo enviado--------")

        except:
            flash('Codigo no existentete', 'warning')
            info="ERROR: codigo no existentete"
            print("!!ERROR: codigo no existentete¡¡")

        datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
        df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
        tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed
        print ("\n\t", tabla_prestamos)

        return render_template("solicitar_equipo.html", info=info, title='Solicitar equipo', tabla_prestamos=tabla_prestamos, segment='Solicitudes')

    #https://blog.hedaro.com/styling-dataframe-tables.html
    datos_prestamos=pd.read_csv('../data/Prestamos v2.csv')
    df1 = datos_prestamos[['CODIGO','NOMBRE','CEDULA','EQUIPO','ACTIVO NUEVO','FECHA']]
    tabla_prestamos = HTML(df1.to_html(classes = 'table table- border table-striped table-hover table-condensed' ))
    print ("\n\t", tabla_prestamos)

    return render_template("solicitar_equipo.html", title='Solicitar equipo', tabla_prestamos=tabla_prestamos, segment='Solicitudes')


@app.route('/solicitud_historial', methods=['GET','POST'])
@login_required
def solicitud_historial():
    if request.method == 'POST':
        print ("\n\n\t\t********************************\n")
        print ("\t\t*    solicitud historial    *\n")
        print ("\t\t********************************\n")

        opcion_1=str(request.form.get('opcion_1'))
        opcion_2=str(request.form.get('opcion_2'))
        opcion_3=str(request.form.get('opcion_3'))
        opcion_4=str(request.form.get('opcion_4'))
        
        opcion_6=str(request.form.get('opcion_6'))
        opcion_7=str(request.form.get('opcion_7'))
        opcion_8=str(request.form.get('opcion_8'))
        cdestinatario=str(request.form.get('cdestinatario'))

        msg = Message('Solicitud de archivos laboratorio ingenieria electronica',
                      sender='noreply@demo.com',
                      recipients=[cdestinatario])

        msg.body = "Cordial saludo, en el presente email se adjunta los archivos solicitados resientementes del laboratorio."

        if opcion_1 == 'si':
            with open("../data/Historial v2.csv", encoding="utf8") as fp:
                msg.attach("Historial de prestamos de equipos.csv", "Historial de prestamos de equipos/csv", fp.read())
        if opcion_2 == 'si':
            with open("../data/Prestamos v2.csv", encoding="utf8") as fp:
                msg.attach("Prestamos actuales.csv", "Prestamos actuales/csv", fp.read())
        if opcion_3 == 'si':
            with open("../data/Base equipos v2.csv", encoding="utf8") as fp:
                msg.attach("Base de datos equipos.csv", "Base de datos equipos/csv", fp.read())
        if opcion_4 == 'si':
            with open("../data/Monitores_id.csv", encoding="utf8") as fp:
                msg.attach("Base de datos monitores.csv", "Base de datos monitores/csv", fp.read())
        


        if opcion_6 == 'si':
            with open("../data/Historial control laboratorio.csv", encoding="utf8") as fp:
                msg.attach("Historial control laboratorio.csv", "Historial control laboratorio/csv", fp.read())
        if opcion_7 == 'si':
            with open("../data/Control laboratorio.csv", encoding="utf8") as fp:
                msg.attach("Base de datos autorizados del control de laboratorio.csv", "Base de datos autorizados del control de laboratorio/csv", fp.read())

        mail.send(msg)

        flash('Archivos enviados', 'success')
        info= "Archivos enviados"
        print("\n-------Solicitud enviada--------")

        return render_template("solicitud_historial.html", info=info, title='Solicitar historial', segment='Solicitudes')

    return render_template("solicitud_historial.html", title='Solicitar historial', segment='Solicitudes')

@app.route('/registro_equipos', methods=['GET','POST'])
@login_required
def registro_equipos():
    if request.method == 'POST':
        # ja  EQUIPO	  MARCA  	MODELO	   ACTIVO NUEVO	    S/N	    ESTADO DE EQUIPO   PAG. INV. OF.  UBICACIÓN
        act_now = str(request.form.get('act_now')) #.decode('utf-8')
        leer_verificacion_equipo_existe= pd.read_csv('../data/Base equipos v2.csv')
        leer_equipo_verificacion = leer_verificacion_equipo_existe['ACTIVO NUEVO'].tolist()
        verificacion_Act_new = act_now in leer_equipo_verificacion

        if verificacion_Act_new is False:

            jaa=pd.DataFrame({'ja':['']})
            act_nowE=pd.DataFrame({'ACTIVO NUEVO':[act_now]})
            dnomE = str(request.form.get('dnomE')) #.decode('utf-8')
            nombreE=pd.DataFrame({'EQUIPO':[dnomE]})
            MarcE = str(request.form.get('MarcE')) #.decode('utf-8')
            marcaE=pd.DataFrame({'MARCA':[MarcE]})
            modeloE = str(request.form.get('modeloE')) #.decode('utf-8')
            ModelE=pd.DataFrame({'MODELO':[modeloE]})
            dserie = str(request.form.get('dserie')) #.decode('utf-8')
            dSerie=pd.DataFrame({'SERIE':[dserie]})
            ncc = str(request.form.get('ncc')) #.decode('utf-8')
            dncc=pd.DataFrame({'NOMBRE CENTRO COSTOS':[ncc]})
            dde = str(request.form.get('dde')) #.decode('utf-8')
            ddescripcion=pd.DataFrame({'DESCRIPCION':[dde]})
            ubiE = str(request.form.get('ubiE')) #.decode('utf-8')
            ubicaE=pd.DataFrame({'UBICACIÓN':[ubiE]})

            datos_estudiantes_lab = pd.concat([jaa, dncc, ubicaE, act_nowE, nombreE, marcaE, ModelE, dSerie, ddescripcion], axis=1,)
            datos_estudiantes_lab.reset_index(drop = True).to_csv('../data/Base equipos v2.csv',header=False, index=False, mode='a')

            flash('Equipo registrado', 'success') # info  success warning
            info = "Equipo registrado"

            datos_equii=pd.read_csv('../data/Base equipos v2.csv')
            dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
            tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_equipos.html", title='Registro de equipos', info=info, tabla_equipos=tabla_equipos, segment='Registro')

        if verificacion_Act_new is True:
            flash('Registro no guardado, el equipo ya existe en la base de datos o ya existe un activo nuevo con este codigo.', 'warning')
            info = "ERROR: Registro no guardado, el equipo ya existe en la base de datos o ya existe un activo nuevo con este codigo."

            datos_equii=pd.read_csv('../data/Base equipos v2.csv')
            dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
            tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_equipos.html", title='Registro de equipos', info=info, tabla_equipos=tabla_equipos, segment='Registro')

    datos_equii=pd.read_csv('../data/Base equipos v2.csv')
    dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
    tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("registro_equipos.html", title='Registro de equipos', tabla_equipos=tabla_equipos, segment='Registro')

@app.route('/registro_monitores', methods=['GET','POST'])
@login_required
def registro_monitores():
    if request.method == 'POST':
        # codigo new verificacion2 de monitores
        codes = int(request.form.get('codes')) #.decode('utf-8')
        leer_verificacion_monitor_existe= pd.read_csv('../data/Monitores_id.csv')
        leer_id_verificacion22 = leer_verificacion_monitor_existe['CODIGO'].tolist()
        verificacion22 = codes in leer_id_verificacion22

        if verificacion22 is False:
            ides = int(request.form.get('ides')) #.decode('utf-8')
            leer_id_verificacionid = leer_verificacion_monitor_existe['ID'].tolist()
            verificacionid = ides in leer_id_verificacionid

            if verificacionid is False:
                codigo_monitor=pd.DataFrame({'CODIGO':[codes]})
                id_monitor=pd.DataFrame({'ID':[ides]})
                nomes = str(request.form.get('nomes')) #.decode('utf-8')
                nombre_monitor=pd.DataFrame({'NOMBRE':[nomes]})
                teles = int(request.form.get('teles')) #.decode('utf-8')
                tel_monitor=pd.DataFrame({'TELEFONO':[teles]})

                datos_monitores_lab = pd.concat([codigo_monitor, nombre_monitor, tel_monitor, id_monitor], axis=1,)
                datos_monitores_lab.reset_index(drop = True).to_csv('../data/Monitores_id.csv',header=False, index=False, mode='a')

                flash('Monitor registrado.', 'success') # info  success warning
                info = "Monitor registrado."

                datos_moni=pd.read_csv('../data/Monitores_id.csv')
                dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
                tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

                return render_template("registro_monitores.html", title='Registro de monitores', info=info, tabla_monitores=tabla_monitores, segment='Registro')

            if verificacionid is True:
                flash('Registro no guardado, la ID ya existe, intente de nuevo.', 'warning')
                info = "ERROR: Registro no guardado, la ID ya existe, intente de nuevo."
                datos_moni=pd.read_csv('../data/Monitores_id.csv')
                dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
                tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed
                return render_template("registro_monitores.html", title='Registro de monitores', info=info, tabla_monitores=tabla_monitores, segment='Registro')

        if verificacion22 is True:
            flash('Registro no guardado, el codigo ya existe en la base de datos.', 'warning')
            info = "ERROR: Registro no guardado, el codigo ya existe en la base de datos."
            datos_moni=pd.read_csv('../data/Monitores_id.csv')
            dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
            tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed
            return render_template("registro_monitores.html", title='Registro de monitores', info=info, tabla_monitores=tabla_monitores, segment='Registro')

    datos_moni=pd.read_csv('../data/Monitores_id.csv')
    dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
    tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("registro_monitores.html", title='Registro de monitores', tabla_monitores=tabla_monitores, segment='Registro')

@app.route('/registro_estudiante', methods=['GET','POST'])
@login_required
def registro_estudiante():
    if request.method == 'POST':
        # codigo new verificacion2 de monitores
        codes_Estu = int(request.form.get('codes_estu')) #.decode('utf-8')
        leer_verificacion_estudiante_existe= pd.read_csv('../data/Estudiantes v2.csv')
        leer_id_verificacion_estu = leer_verificacion_estudiante_existe['CODIGO'].tolist()
        verificacion_estu = codes_Estu in leer_id_verificacion_estu

        if verificacion_estu is False:

            codigo_estudiante=pd.DataFrame({'CODIGO':[codes_Estu]})
            nomes_estu = str(request.form.get('nomes_estu')) #.decode('utf-8')
            nombre_estudiante=pd.DataFrame({'NOMBRE':[nomes_estu]})
            cedull = int(request.form.get('cedull')) #.decode('utf-8')
            cedula_estudiante=pd.DataFrame({'CEDULA':[cedull]})
            email_estuuu = str(codes_Estu) + "@estudiantesunibague.edu.co"
            correo_estudiante = pd.DataFrame({'CORREO':[email_estuuu]})

            datos_estudiante_new = pd.concat([codigo_estudiante, nombre_estudiante, cedula_estudiante, correo_estudiante], axis=1,)
            datos_estudiante_new.reset_index(drop = True).to_csv('../data/Estudiantes v2.csv',header=False, index=False, mode='a')

            flash('Estudiante registrado.', 'success') # info  success warning
            info = "Estudiante registrado."

            datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
            dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
            tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_estudiante.html", title='Registro de estudiante', info=info, tabla_estudiantes=tabla_estudiantes, segment='Registro')

        if verificacion_estu is True:
            flash('Registro no guardado, el codigo ya existe en la base de datos.', 'warning')
            info = "ERROR: Registro no guardado, el codigo ya existe en la base de datos."

            datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
            dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
            tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_estudiante.html", title='Registro de estudiante', info=info, tabla_estudiantes=tabla_estudiantes, segment='Registro')

    datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
    dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
    tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("registro_estudiante.html", title='Registro de estudiante', tabla_estudiantes=tabla_estudiantes, segment='Registro')

@app.route('/registro_control_laboratorio', methods=['GET','POST'])
@login_required
def registro_control_laboratorio():
    if request.method == 'POST':

        cual_lab = str(request.form.get('cual_lab'))
        codes_Estu_rcl = int(request.form.get('codes_estu_rc'))

        leer_verificacion_estudiante_existe_rc= pd.read_csv('../data/Control laboratorio.csv')
        datos_laboratorio_solicitado = leer_verificacion_estudiante_existe_rc.loc[(leer_verificacion_estudiante_existe_rc)['LABORATORIO'] == cual_lab]

        leer_id_verificacion_estu_rc = datos_laboratorio_solicitado['CODIGO'].tolist()
        verificacion_estu_rc = codes_Estu_rcl in leer_id_verificacion_estu_rc

        if verificacion_estu_rc is False:

            codigo_estudiante_rc=pd.DataFrame({'CODIGO':[codes_Estu_rcl]})
            nomes_estu_rc = str(request.form.get('nomes_estu_rc'))
            nombre_estudiante_rc=pd.DataFrame({'NOMBRE':[nomes_estu_rc]})
            telestud_rc = int(request.form.get('telestu_rc'))
            telefono_estudiante=pd.DataFrame({'TELEFONO':[telestud_rc]})
            laboratorio_est=pd.DataFrame({'LABORATORIO':[cual_lab]})

            datos_estu_nuevo = leer_verificacion_estudiante_existe_rc.loc[(leer_verificacion_estudiante_existe_rc)['CODIGO'] == codes_Estu_rcl]
            datos_estu_nuevo_o_no = datos_estu_nuevo['CODIGO'].tolist()
            datos_estu_nuevo_o_no_verif = codes_Estu_rcl in datos_estu_nuevo_o_no

            if datos_estu_nuevo_o_no_verif is False:
                clave_random_serial = generate(3,'', 7, 7,type_of_value = 'hex', capital = 'mix', seed = None).get_key()
                serial_estu = str(codes_Estu_rcl) + str(clave_random_serial)

            if datos_estu_nuevo_o_no_verif is True:
                serial_estu = datos_estu_nuevo['SERIAL'].iloc[0]

            serial_estu_rc = pd.DataFrame({'SERIAL':[serial_estu]})

            dateinilunes = request.form.get('dateinilunes')
            dateinilunes_rc=pd.DataFrame({'FECHA INICIAL LUNES':[dateinilunes]})
            datefinlunes = request.form.get('datefinlunes')
            datefinlunes_rc=pd.DataFrame({'FECHA FINAL LUNES':[datefinlunes]})
            horainilunes = request.form.get('horainilunes')
            horainilunes_rc=pd.DataFrame({'HORA INICIAL LUNES':[horainilunes]})
            horafinlunes = request.form.get('horafinlunes')
            horafinlunes_rc=pd.DataFrame({'HORA FINAL LUNES':[horafinlunes]})

            dateinimartes = request.form.get('dateinimartes')
            dateinimartes_rc=pd.DataFrame({'FECHA INICIAL MARTES':[dateinimartes]})
            datefinmartes = request.form.get('datefinmartes')
            datefinmartes_rc=pd.DataFrame({'FECHA FINAL MARTES':[datefinmartes]})
            horainimartes = request.form.get('horainimartes')
            horainimartes_rc=pd.DataFrame({'HORA INICIAL MARTES':[horainimartes]})
            horafinmartes = request.form.get('horafinmartes')
            horafinmartes_rc=pd.DataFrame({'HORA FINAL MARTES':[horafinmartes]})

            dateinimiercoles = request.form.get('dateinimiercoles')
            dateinimiercoles_rc=pd.DataFrame({'FECHA INICIAL MIERCOLES':[dateinimiercoles]})
            datefinmiercoles = request.form.get('datefinmiercoles')
            datefinmiercoles_rc=pd.DataFrame({'FECHA FINAL MIERCOLES':[datefinmiercoles]})
            horainimiercoles = request.form.get('horainimiercoles')
            horainimiercoles_rc=pd.DataFrame({'HORA INICIAL MIERCOLES':[horainimiercoles]})
            horafinmiercoles = request.form.get('horafinmiercoles')
            horafinmiercoles_rc=pd.DataFrame({'HORA FINAL MIERCOLES':[horafinmiercoles]})

            dateinijueves = request.form.get('dateinijueves')
            dateinijueves_rc=pd.DataFrame({'FECHA INICIAL JUEVES':[dateinijueves]})
            datefinjueves = request.form.get('datefinjueves')
            datefinjueves_rc=pd.DataFrame({'FECHA FINAL JUEVES':[datefinjueves]})
            horainijueves = request.form.get('horainijueves')
            horainijueves_rc=pd.DataFrame({'HORA INICIAL JUEVES':[horainijueves]})
            horafinjueves = request.form.get('horafinjueves')
            horafinjueves_rc=pd.DataFrame({'HORA FINAL JUEVES':[horafinjueves]})

            dateiniviernes = request.form.get('dateiniviernes')
            dateiniviernes_rc=pd.DataFrame({'FECHA INICIAL VIERNES':[dateiniviernes]})
            datefinviernes = request.form.get('datefinviernes')
            datefinviernes_rc=pd.DataFrame({'FECHA FINAL VIERNES':[datefinviernes]})
            horainiviernes = request.form.get('horainiviernes')
            horainiviernes_rc=pd.DataFrame({'HORA INICIAL VIERNES':[horainiviernes]})
            horafinviernes = request.form.get('horafinviernes')
            horafinviernes_rc=pd.DataFrame({'HORA FINAL VIERNES':[horafinviernes]})

            dateinisabado = request.form.get('dateinisabado')
            dateinisabado_rc=pd.DataFrame({'FECHA INICIAL SABADO':[dateinisabado]})
            datefinsabado = request.form.get('datefinsabado')
            datefinsabado_rc=pd.DataFrame({'FECHA FINAL SABADO':[datefinsabado]})
            horainisabado = request.form.get('horainisabado')
            horainisabado_rc=pd.DataFrame({'HORA INICIAL SABADO':[horainisabado]})
            horafinsabado = request.form.get('horafinsabado')
            horafinsabado_rc=pd.DataFrame({'HORA FINAL SABADO':[horafinsabado]})

            dateinidomingo = request.form.get('dateinidomingo')
            dateinidomingo_rc=pd.DataFrame({'FECHA INICIAL DOMINGO':[dateinidomingo]})
            datefindomingo = request.form.get('datefindomingo')
            datefindomingo_rc=pd.DataFrame({'FECHA FINAL DOMINGO':[datefindomingo]})
            horainidomingo = request.form.get('horainidomingo')
            horainidomingo_rc=pd.DataFrame({'HORA INICIAL DOMINGO':[horainidomingo]})
            horafindomingo = request.form.get('horafindomingo')
            horafindomingo_rc=pd.DataFrame({'HORA FINAL DOMINGO':[horafindomingo]})


            datos_estudiante_fecha = pd.concat([codigo_estudiante_rc, nombre_estudiante_rc, serial_estu_rc, telefono_estudiante, laboratorio_est, dateinilunes_rc, datefinlunes_rc, horainilunes_rc, horafinlunes_rc, dateinimartes_rc, datefinmartes_rc, horainimartes_rc, horafinmartes_rc, dateinimiercoles_rc, datefinmiercoles_rc, horainimiercoles_rc, horafinmiercoles_rc, dateinijueves_rc, datefinjueves_rc, horainijueves_rc, horafinjueves_rc, dateiniviernes_rc, datefinviernes_rc, horainiviernes_rc, horafinviernes_rc, dateinisabado_rc, datefinsabado_rc, horainisabado_rc, horafinsabado_rc, dateinidomingo_rc, datefindomingo_rc, horainidomingo_rc, horafindomingo_rc], axis=1,)

            print(datos_estudiante_fecha)

            datos_estudiante_fecha.reset_index(drop = True).to_csv('../data/Control laboratorio.csv',header=False, index=False, mode='a')

            flash('Estudiante registrado.', 'success') # info  success warning
            info = "Estudiante "+nomes_estu_rc+" registrado. El serial del etudiante se encuentra a lo ultimo de la tabla inferior en la columna SERIAL"

            datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
            dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
            tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_control_laboratorio.html", title='Registro control de lab', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Registro')

        if verificacion_estu_rc is True:
            flash('Registro no guardado, el codigo ya existe en la base de datos para este Laboratorio.', 'warning')
            info = "ERROR: Registro no guardado, el codigo ya existe en la base de datos para este Laboratorio."

            datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
            dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
            tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("registro_control_laboratorio.html", title='Registro control de lab', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Registro')

    datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
    dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
    tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("registro_control_laboratorio.html", title='Registro control de lab', tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Registro')

@app.route('/new_base_estudiantes', methods=['GET','POST'])
@login_required
def new_base_estudiantes():
    if request.method == 'POST':

        cadestinatario=str(request.form.get('cadestinatario'))
        #fecha = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())

        msg = Message('Base de datos anterior de estudiantes de ingenieria electronica',
                      sender='noreply@demo.com',
                      recipients=[cadestinatario])

        msg.body = "Cordial saludo, en el presente email se adjunta la base de datos anterior de los estudiantes de ingenieria electronica."

        with open("../data/Estudiantes v2.csv") as fp:
            #msg.attach("Base de datos estudiantes "+str(fecha)+".csv", "Base de datos estudiantes "+str(fecha)+ "/csv", fp.read())
            msg.attach("Base de datos estudiantes antigua.csv", "Base de datos estudiantes antigua/csv", fp.read())

        try:
            archivo_new = request.files["archivo"]
            dat_nbe=pd.read_csv(archivo_new)
            print("leyo el archivo")
            mail.send(msg)

            dat_nbe["ja"] = ""
            dat_nbe.columns = ['CODIGO','NOMBRE','CEDULA','CORREO','ja']

            print(dat_nbe["CODIGO"])
            remove("../data/Estudiantes v2.csv")
            dat_nbe.reset_index(drop = True).to_csv('../data/Estudiantes v2.csv',header=True, index=False)
            print("guardo el archivo")
            flash('Base de datos registrada y archivo anterior enviado.', 'success') # info  success warning
            info = "Base de datos registrada y archivo anterior enviado."

        except:
            flash('El archivo no cumple con los parametros o formato necesario, por favor revise e intente de nuevo', 'warning') # info  success warning
            info= "ERROR: El archivo no cumple con los parametros o formato necesario, por favor revise e intente de nuevo"
            print ("\n\n!!!!!ERROR: El archivo no cumple con los parametros o formato necesario, por favor revise e intente de nuevo")
            return render_template("new_base_estudiantes.html", title='Registro Base de estudiantes', info=info, segment='Registro')

        return render_template("new_base_estudiantes.html", title='Registro Base de estudiantes',info=info, segment='Registro')

    return render_template("new_base_estudiantes.html", title='Registro Base de estudiantes', segment='Registro')


@app.route('/eliminar_estudiante', methods=['GET','POST'])
@login_required
def eliminar_estudiante():
    if request.method == 'POST':

        eliminar_estudiante = int(request.form.get('eliestu')) #.decode('utf-8')
        dat_estudiant=pd.read_csv('../data/Estudiantes v2.csv')
        leer_cod_esta = dat_estudiant['CODIGO'].tolist()
        estudiante_esta = eliminar_estudiante in leer_cod_esta

        if estudiante_esta is True:
            eliminarmonitor=dat_estudiant.loc[(dat_estudiant)['CODIGO']!=eliminar_estudiante]
            eliminarmonitor.reset_index(drop = True).to_csv('../data/Estudiantes v2.csv',header=True, index=False)

            flash('Estudiante eliminado', 'success') # info  success warning
            info = "Estudiante eliminado"

            datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
            dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
            tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_estudiante.html", title='Eliminar estudiante', info=info, tabla_estudiantes=tabla_estudiantes, segment='Eliminar')

        if estudiante_esta is False:
            flash('El código ingresado no corresponde con algún estudiante existente, intenta de nuevo', 'warning') # info  success warning
            info = "El código ingresado no corresponde con algún estudiante existente, intenta de nuevo"

            datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
            dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
            tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_estudiante.html", title='Eliminar estudiante', info=info, tabla_estudiantes=tabla_estudiantes, segment='Eliminar')

    datos_estud=pd.read_csv('../data/Estudiantes v2.csv')
    dfestu = datos_estud[['CODIGO','NOMBRE','CEDULA','CORREO']]
    tabla_estudiantes = HTML(dfestu.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("eliminar_estudiante.html", title='Eliminar estudiante', tabla_estudiantes=tabla_estudiantes, segment='Eliminar')

@app.route('/eliminar_monitores', methods=['GET','POST'])
@login_required
def eliminar_monitores():
    if request.method == 'POST':

        eliminar_moni = int(request.form.get('elimoni')) #.decode('utf-8')
        dat_monitor=pd.read_csv('../data/Monitores_id.csv')
        leer_cod_esta = dat_monitor['CODIGO'].tolist()
        monitor_esta = eliminar_moni in leer_cod_esta

        if monitor_esta is True:
            eliminarmonitor=dat_monitor.loc[(dat_monitor)['CODIGO']!=eliminar_moni]
            eliminarmonitor.reset_index(drop = True).to_csv('../data/Monitores_id.csv',header=True, index=False)

            flash('Monitor eliminado', 'success') # info  success warning
            info = "Monitor eliminado"

            datos_moni=pd.read_csv('../data/Monitores_id.csv')
            dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
            tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_monitores.html", title='Eliminar monitores', info=info, tabla_monitores=tabla_monitores, segment='Eliminar')

        if monitor_esta is False:
            flash('El código ingresado no corresponde con algún monitor existente, intenta de nuevo', 'warning') # info  success warning
            info = "El código ingresado no corresponde con algún monitor existente, intenta de nuevo"

            datos_moni=pd.read_csv('../data/Monitores_id.csv')
            dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
            tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_monitores.html", title='Eliminar monitores', info=info, tabla_monitores=tabla_monitores, segment='Eliminar')

    datos_moni=pd.read_csv('../data/Monitores_id.csv')
    dfmoni = datos_moni[['CODIGO','NOMBRE','TELEFONO','ID']]
    tabla_monitores = HTML(dfmoni.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("eliminar_monitores.html", title='Eliminar monitores', tabla_monitores=tabla_monitores, segment='Eliminar')

@app.route('/eliminar_equipos', methods=['GET','POST'])
@login_required
def eliminar_equipos():
    if request.method == 'POST':

        eliminar_equi = str(request.form.get('eliequi')) #.decode('utf-8')
        dat_equipo=pd.read_csv('../data/Base equipos v2.csv')
        leer_cod_esta = dat_equipo['ACTIVO NUEVO'].tolist()
        equi_esta = eliminar_equi in leer_cod_esta

        if equi_esta is True:
            eliminarequipo=dat_equipo.loc[(dat_equipo)['ACTIVO NUEVO']!=eliminar_equi]
            eliminarequipo.reset_index(drop = True).to_csv('../data/Base equipos v2.csv',header=True, index=False)

            flash('Equipo eliminado', 'success') # info  success warning
            info = "Equipo eliminado"

            datos_equii=pd.read_csv('../data/Base equipos v2.csv')
            dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
            tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_equipos.html", title='Eliminar equipos', info=info, tabla_equipos=tabla_equipos, segment='Eliminar')

        if equi_esta is False:
            flash('El código ingresado no corresponde con algún equipo existente, intenta de nuevo', 'warning') # info  success warning
            info = "El código ingresado no corresponde con algún equipo existente, intenta de nuevo"

            datos_equii=pd.read_csv('../data/Base equipos v2.csv')
            dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
            tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_equipos.html", title='Eliminar equipos', info=info, tabla_equipos=tabla_equipos, segment='Eliminar')

    datos_equii=pd.read_csv('../data/Base equipos v2.csv')
    dfequi = datos_equii[['NOMBRE CENTRO COSTOS','UBICACION','ACTIVO NUEVO','EQUIPO','MARCA','MODELO','SERIE']]
    tabla_equipos = HTML(dfequi.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("eliminar_equipos.html", title='Eliminar equipos', tabla_equipos=tabla_equipos, segment='Eliminar')

@app.route('/eliminar_estud_control_lab', methods=['GET','POST'])
@login_required
def eliminar_estud_control_lab():
    if request.method == 'POST':

        eliminar_estudiante_control = int(request.form.get('eliestu_control'))
        cual_lab = str(request.form.get('cual_lab'))

        dat_estudiant_control=pd.read_csv('../data/Control laboratorio.csv')
        datos_laboratorio_eliminar = dat_estudiant_control.loc[(dat_estudiant_control)['LABORATORIO'] == cual_lab]

        leer_cod_esta_control = datos_laboratorio_eliminar['CODIGO'].tolist()
        estudiante_esta_control = eliminar_estudiante_control in leer_cod_esta_control

        if estudiante_esta_control is True:

            index_est_eliminar = datos_laboratorio_eliminar.index[(datos_laboratorio_eliminar)['CODIGO'] == eliminar_estudiante_control].tolist()
            eliminaretu_controllab=dat_estudiant_control.drop(dat_estudiant_control.index[index_est_eliminar])
            #eliminaretu_controllab=dat_estudiant_control.loc[(dat_estudiant_control)['CODIGO']!=eliminar_estudiante_control]
            eliminaretu_controllab.reset_index(drop = True).to_csv('../data/Control laboratorio.csv',header=True, index=False)

            flash('Estudiante eliminado', 'success') # info  success warning
            info = "Estudiante "+str(eliminar_estudiante_control)+" eliminado"+" del laboratorio "+str(cual_lab)

            datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
            dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
            tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_estud_control_lab.html", title='Eliminar estud control lab', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Eliminar')

        if estudiante_esta_control is False:
            flash('El código ingresado o el laboratorio no corresponde con algún estudiante existente, intenta de nuevo', 'warning') # info  success warning
            info = "El código "+str(eliminar_estudiante_control)+" ingresado en el laboratorio "+str(cual_lab)+" no corresponde con algún estudiante existente, intenta de nuevo"

            datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
            dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
            tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("eliminar_estud_control_lab.html", title='Eliminar estud control lab', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Eliminar')

    datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
    dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
    tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("eliminar_estud_control_lab.html", title='Eliminar estud control lab', tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Eliminar')


@app.route('/Controlmanuallaboratorio', methods=['GET','POST'])
@login_required
def Controlmanuallaboratorio():

    if request.method == 'POST':
        cual_lab_admin = str(request.form.get('cual_lab_admin'))

        #--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
        if cual_lab_admin == 'Laboratorio 1':
            ip_cliente_manual = 'IP'   
            puerto_cliente_manual = 5050
            print('Ip y puerto del Laboratorio 1')

        if cual_lab_admin == 'Laboratorio 2':
            ip_cliente_manual = 'IP'
            puerto_cliente_manual = 5050
            print('Ip y puerto del Laboratorio 2')

        if cual_lab_admin == 'Laboratorio 3':
            ip_cliente_manual = 'IP'
            puerto_cliente_manual = 5050
            print('Ip y puerto del Laboratorio 3')

        if cual_lab_admin == 'Laboratorio 4':
            ip_cliente_manual = 'IP'
            puerto_cliente_manual = 5050
            print('Ip y puerto del Laboratorio 4')

        if cual_lab_admin == 'Laboratorio 5':
            ip_cliente_manual = 'IP'
            puerto_cliente_manual = 5050
            print('Ip y puerto del Laboratorio 5')
        #----------------------------------------------------------------------------------------------
        time.sleep(10) #tiempo de espera antes de abrir puerta
        try:
            nombre_admin_controllab = pd.DataFrame({'NOMBRE':['Administrador']})
            cual_lab_rasdfcontrol = pd.DataFrame({'LABORATORIO':[cual_lab_admin]})
            estado_df_control = pd.DataFrame({'ESTADO':['Autorizado']})
            fecha_registro_controllab = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            fecha_registro_df_estado_df_control = pd.DataFrame({'FECHA':[fecha_registro_controllab]})
            espacio_df_control = pd.DataFrame({'':['']})

            try:
                client_ser = socket.socket()
                client_ser.connect((ip_cliente_manual,puerto_cliente_manual))
                print('\nConectado con el servidor')

                peticion_serv = client_ser.recv(1024)
                print(peticion_serv.decode("utf-8") )
                print('Peticion recibida')
                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                client_ser.send(estado_client)
                print("Respuesta enviada satisfactoriamente")
                client_ser.close()
                print("Conexión cerrada con el servidor\n")

            except:
                nombre_admin_controllab = pd.DataFrame({'NOMBRE':['Administrador']})
                cual_lab_rasdfcontrol = pd.DataFrame({'LABORATORIO':[cual_lab_admin]})
                estado_df_control = pd.DataFrame({'ESTADO':['Denegado por no conexion con el cliente-servidor']})
                fecha_registro_controllab = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
                fecha_registro_df_estado_df_control = pd.DataFrame({'FECHA':[fecha_registro_controllab]})
                espacio_df_control = pd.DataFrame({'':['']})

                informacion_historial_control_lab = pd.concat([espacio_df_control,nombre_admin_controllab,espacio_df_control,espacio_df_control,cual_lab_rasdfcontrol,estado_df_control,fecha_registro_df_estado_df_control], axis=1)
                informacion_historial_control_lab.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                flash('No se pudo establecer conexion con el cliente-servidor, intente nuevamente ', 'warning') # info  success warning
                info = 'No se pudo establecer conexion con el cliente-servidor, intente nuevamente '
                print ("\n No se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")

                datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
                dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

                return render_template("Controlmanuallaboratorio.html", title='Control manual laboratorio', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Controlmanuallaboratorio')

        except:

            nombre_admin_controllab = pd.DataFrame({'NOMBRE':['Administrador']})
            cual_lab_rasdfcontrol = pd.DataFrame({'LABORATORIO':[cual_lab_admin]})
            estado_df_control = pd.DataFrame({'ESTADO':['Denegado por no obtener informacion para el historial']})
            fecha_registro_controllab = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            fecha_registro_df_estado_df_control = pd.DataFrame({'FECHA':[fecha_registro_controllab]})
            espacio_df_control = pd.DataFrame({'':['']})

            informacion_historial_control_lab = pd.concat([espacio_df_control,nombre_admin_controllab,espacio_df_control,espacio_df_control,cual_lab_rasdfcontrol,estado_df_control,fecha_registro_df_estado_df_control], axis=1)
            informacion_historial_control_lab.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

            flash('No se pudo obtener informacion para el historial, intente nuevamente ', 'warning') # info  success warning
            info = 'No se pudo obtener informacion para el historial, intente nuevamente '
            print ("\n No se pudo obtener informacion para el historial, intente nuevamente \n")

            datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
            dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
            tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

            return render_template("Controlmanuallaboratorio.html", title='Control manual laboratorio', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Controlmanuallaboratorio')

        informacion_historial_control_lab = pd.concat([espacio_df_control,nombre_admin_controllab,espacio_df_control,espacio_df_control,cual_lab_rasdfcontrol,estado_df_control,fecha_registro_df_estado_df_control], axis=1)
        informacion_historial_control_lab.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

        flash('Laboratorio abierto', 'success')
        info = "El "+str(cual_lab_admin) +" se abrio"
        print ("\n Laboratorio abierto \n")

        datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
        dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
        tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

        return render_template("Controlmanuallaboratorio.html", title='Control manual laboratorio', info=info, tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Controlmanuallaboratorio')

    datos_estud_autorizado=pd.read_csv('../data/Control laboratorio.csv')
    dfestu_autorizado = datos_estud_autorizado[['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
    tabla_estudiantes_autorizado = HTML(dfestu_autorizado.to_html(classes = 'table table- border table-striped table-hover table-condensed' )) #table table-hover,   table-striped table- border -table-hover table-condensed

    return render_template("Controlmanuallaboratorio.html", title='Control manual laboratorio', tabla_estudiantes_autorizado=tabla_estudiantes_autorizado, segment='Controlmanuallaboratorio')

@app.route('/Controllaboratorio', methods=['GET','POST'])
def Controllaboratorio():

    if request.method == 'POST':
        cod_serial = str(request.form.get('cod_serial_html'))           # codigo verificacion de serial
        cual_lab_ras = str(request.form.get('cual_lab_ras'))

        leer_data_control_lab= pd.read_csv('../data/Control laboratorio.csv')
        leer_data_control_lab_selec = leer_data_control_lab.loc[(leer_data_control_lab)['LABORATORIO'] == cual_lab_ras]
        leer_data_control_lab_selec = leer_data_control_lab_selec.reset_index(drop=True) #resetar el index para poder contatenar dataframe correctamente
        print(leer_data_control_lab_selec[['SERIAL','LABORATORIO']])

        leer_control_lab = leer_data_control_lab_selec['SERIAL'].tolist()
        verificacion_serial = cod_serial in leer_control_lab

        fecha_registro = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        #print(datetime.today().weekday()) #optener el dia de la semana 0 = lunes, 6 = domingo
        #temp = pd.Timestamp(datetime.now().strftime('%Y-%m-%d')) #optener el dia de la semana 0 = lunes, 6 = domingo, de unua fecha
        #print(temp.dayofweek)

        #--------------------------- IP y Puerto de las diferentes raspberrys ------------------------
        if cual_lab_ras == 'Laboratorio 1':
            ip_cliente = 'IP'           
            puerto_cliente = 5050
            print('IP y Puerto del Laboratorio 1')

        if cual_lab_ras == 'Laboratorio 2':
            ip_cliente = 'IP'
            puerto_cliente = 5050
            print('IP y Puerto del Laboratorio 2')

        if cual_lab_ras == 'Laboratorio 3':
            ip_cliente = 'IP'
            puerto_cliente = 5050
            print('IP y Puerto del Laboratorio 3')

        if cual_lab_ras == 'Laboratorio 4':
            ip_cliente = 'IP'
            puerto_cliente = 5050
            print('IP y Puerto del Laboratorio 4')

        if cual_lab_ras == 'Laboratorio 5':
            ip_cliente = 'IP'
            puerto_cliente = 5050
            print('IP y Puerto del Laboratorio 5')
        #----------------------------------------------------------------------------------------------

        if verificacion_serial is True:

            alumno_data = leer_data_control_lab_selec.loc[(leer_data_control_lab_selec)['SERIAL'] == cod_serial]

            solo_fecha_actual = datetime.now().strftime('%Y-%m-%d')
            solo_hora_actual = datetime.now().strftime('%H:%M')
            dia_semana_actual = pd.Timestamp(solo_fecha_actual)     #optener el dia de la semana 0 = lunes, 6 = domingo, de unua fecha
            num_dia_semana_actual = dia_semana_actual.dayofweek     #0 = lunes, 6 = domingo

            if num_dia_semana_actual == 0:

                alumno_data_fechaini_lunes = alumno_data.loc[:,'FECHA INICIAL LUNES'].item()
                alumno_data_fechafin_lunes = alumno_data.loc[:,'FECHA FINAL LUNES'].item()
                alumno_data_horaini_lunes = alumno_data.loc[:,'HORA INICIAL LUNES'].item()
                alumno_data_horafin_lunes = alumno_data.loc[:,'HORA FINAL LUNES'].item()

                if pd.isna(alumno_data_fechaini_lunes) is False and pd.isna(alumno_data_fechafin_lunes) is False and pd.isna(alumno_data_horaini_lunes) is False and pd.isna(alumno_data_horafin_lunes) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_lunes <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_lunes:
                        if alumno_data_horaini_lunes <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_lunes:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            print(informacion_alumno_data_historial)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente ', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente '
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente  \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 1:

                alumno_data_fechaini_martes = alumno_data.loc[:,'FECHA INICIAL MARTES'].item()
                alumno_data_fechafin_martes = alumno_data.loc[:,'FECHA FINAL MARTES'].item()
                alumno_data_horaini_martes = alumno_data.loc[:,'HORA INICIAL MARTES'].item()
                alumno_data_horafin_martes = alumno_data.loc[:,'HORA FINAL MARTES'].item()

                if pd.isna(alumno_data_fechaini_martes) is False and pd.isna(alumno_data_fechafin_martes) is False and pd.isna(alumno_data_horaini_martes) is False and pd.isna(alumno_data_horafin_martes) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_martes <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_martes:
                        if alumno_data_horaini_martes <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_martes:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 2:

                alumno_data_fechaini_miercoles = alumno_data.loc[:,'FECHA INICIAL MIERCOLES'].item()
                alumno_data_fechafin_miercoles = alumno_data.loc[:,'FECHA FINAL MIERCOLES'].item()
                alumno_data_horaini_miercoles = alumno_data.loc[:,'HORA INICIAL MIERCOLES'].item()
                alumno_data_horafin_miercoles = alumno_data.loc[:,'HORA FINAL MIERCOLES'].item()

                if pd.isna(alumno_data_fechaini_miercoles) is False and pd.isna(alumno_data_fechafin_miercoles) is False and pd.isna(alumno_data_horaini_miercoles) is False and pd.isna(alumno_data_horafin_miercoles) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_miercoles <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_miercoles:
                        if alumno_data_horaini_miercoles <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_miercoles:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 3:

                alumno_data_fechaini_jueves = alumno_data.loc[:,'FECHA INICIAL JUEVES'].item()
                alumno_data_fechafin_jueves = alumno_data.loc[:,'FECHA FINAL JUEVES'].item()
                alumno_data_horaini_jueves = alumno_data.loc[:,'HORA INICIAL JUEVES'].item()
                alumno_data_horafin_jueves = alumno_data.loc[:,'HORA FINAL JUEVES'].item()

                if pd.isna(alumno_data_fechaini_jueves) is False and pd.isna(alumno_data_fechafin_jueves) is False and pd.isna(alumno_data_horaini_jueves) is False and pd.isna(alumno_data_horafin_jueves) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_jueves <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_jueves:
                        if alumno_data_horaini_jueves <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_jueves:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 4:

                alumno_data_fechaini_viernes = alumno_data.loc[:,'FECHA INICIAL VIERNES'].item()
                alumno_data_fechafin_viernes = alumno_data.loc[:,'FECHA FINAL VIERNES'].item()
                alumno_data_horaini_viernes = alumno_data.loc[:,'HORA INICIAL VIERNES'].item()
                alumno_data_horafin_viernes = alumno_data.loc[:,'HORA FINAL VIERNES'].item()

                if pd.isna(alumno_data_fechaini_viernes) is False and pd.isna(alumno_data_fechafin_viernes) is False and pd.isna(alumno_data_horaini_viernes) is False and pd.isna(alumno_data_horafin_viernes) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_viernes <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_viernes:
                        if alumno_data_horaini_viernes <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_viernes:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 5:

                alumno_data_fechaini_sabado = alumno_data.loc[:,'FECHA INICIAL SABADO'].item()
                alumno_data_fechafin_sabado = alumno_data.loc[:,'FECHA FINAL SABADO'].item()
                alumno_data_horaini_sabado = alumno_data.loc[:,'HORA INICIAL SABADO'].item()
                alumno_data_horafin_sabado = alumno_data.loc[:,'HORA FINAL SABADO'].item()

                if pd.isna(alumno_data_fechaini_sabado) is False and pd.isna(alumno_data_fechafin_sabado) is False and pd.isna(alumno_data_horaini_sabado) is False and pd.isna(alumno_data_horafin_sabado) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_sabado <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_sabado:
                        if alumno_data_horaini_sabado <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_sabado:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

            if num_dia_semana_actual == 6:

                alumno_data_fechaini_domingo = alumno_data.loc[:,'FECHA INICIAL DOMINGO'].item()
                alumno_data_fechafin_domingo = alumno_data.loc[:,'FECHA FINAL DOMINGO'].item()
                alumno_data_horaini_domingo = alumno_data.loc[:,'HORA INICIAL DOMINGO'].item()
                alumno_data_horafin_domingo = alumno_data.loc[:,'HORA FINAL DOMINGO'].item()

                if pd.isna(alumno_data_fechaini_domingo) is False and pd.isna(alumno_data_fechafin_domingo) is False and pd.isna(alumno_data_horaini_domingo) is False and pd.isna(alumno_data_horafin_domingo) is False: #para  mirar si son nan, osea que no tienen nada
                    if alumno_data_fechaini_domingo <= solo_fecha_actual and solo_fecha_actual <= alumno_data_fechafin_domingo:
                        if alumno_data_horaini_domingo <= solo_hora_actual and solo_hora_actual <= alumno_data_horafin_domingo:

                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df = pd.DataFrame({'ESTADO':['Autorizado']})
                            fecha_registro_df = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_alumno_data_historial = pd.concat([alumno_data_historial,estado_df,fecha_registro_df], axis=1)
                            #se comunica con el servidor
                            try:
                                try:
                                    client_ser = socket.socket()
                                    client_ser.connect((ip_cliente,puerto_cliente))
                                    print('\nConectado con el servidor')

                                except:
                                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado no se pudo establecer conexion con el cliente-servidor']})
                                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})

                                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                    flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                    info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                    print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente\n")
                                    return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                                peticion_serv = client_ser.recv(1024)
                                print(peticion_serv.decode("utf-8") )
                                print('Peticion recibida')
                                estado_client = b"AUT0R1ZAD0entradaFASTPEL"
                                client_ser.send(estado_client)
                                print("Respuesta enviada satisfactoriamente")
                                client_ser.close()
                                print("Conexión cerrada con el servidor\n")

                                informacion_alumno_data_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                                flash('INGRESO AUTORIZADO', 'success') # info  success warning
                                info = "Ingreso AUTORIZADO para: "+ str(informacion_alumno_data_historial.iloc[0,1])+' el dia: '+ str(fecha_registro)
                                print ("\n\t Ingreso AUTORIZADO para: ", informacion_alumno_data_historial.iloc[0,1],' el dia: ', fecha_registro)

                            except:
                                flash('Ingreso DENEGADO intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO intente nuevamente'
                                print ("\n Ingreso DENEGADO intente nuevamente \n")

                        else:
                            alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por hora no autorizada']})
                            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                            informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                            try:
                                client_ser = socket.socket()
                                client_ser.connect((ip_cliente,puerto_cliente))
                                print('\nConectado con el servidor')

                            except:
                                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                            peticion_serv = client_ser.recv(1024)
                            print(peticion_serv.decode("utf-8") )
                            print('Peticion recibida')
                            estado_client = b"D3N3G4D0entradaFASTPEL"
                            client_ser.send(estado_client)
                            print("Respuesta enviada satisfactoriamente")
                            client_ser.close()
                            print("Conexión cerrada con el servidor\n")

                            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                            flash('Ingreso DENEGADO no tienes autorizacion para esta hora', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no tienes autorizacion para esta hora'
                            print ("\n Ingreso DENEGADO no tienes autorizacion para esta hora \n")

                    else:
                        alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                        estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por autorizacion vencida']})
                        fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                        informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)

                        try:
                            client_ser = socket.socket()
                            client_ser.connect((ip_cliente,puerto_cliente))
                            print('\nConectado con el servidor')

                        except:
                            flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                            info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                            print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                        peticion_serv = client_ser.recv(1024)
                        print(peticion_serv.decode("utf-8") )
                        print('Peticion recibida')
                        estado_client = b"D3N3G4D0entradaFASTPEL"
                        client_ser.send(estado_client)
                        print("Respuesta enviada satisfactoriamente")
                        client_ser.close()
                        print("Conexión cerrada con el servidor\n")

                        informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                        flash('Ingreso DENEGADO su fecha de autorizacion a vencido', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO su fecha de autorizacion a vencido'
                        print ("\n Ingreso DENEGADO su fecha de autorizacion a vencido \n")
                else:
                    alumno_data_historial = alumno_data.loc[:,['CODIGO','NOMBRE','SERIAL','TELEFONO','LABORATORIO']]
                    estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado por dia no autorizado']})
                    fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
                    informacion_denegado_historial = pd.concat([alumno_data_historial,estado_df_denegado,fecha_registro_df_denegado], axis=1)
                    try:
                        client_ser = socket.socket()
                        client_ser.connect((ip_cliente,puerto_cliente))
                        print('\nConectado con el servidor')

                    except:
                        flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                        info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                        print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

                    peticion_serv = client_ser.recv(1024)
                    print(peticion_serv.decode("utf-8") )
                    print('Peticion recibida')
                    estado_client = b"D3N3G4D0entradaFASTPEL"
                    client_ser.send(estado_client)
                    print("Respuesta enviada satisfactoriamente")
                    client_ser.close()
                    print("Conexión cerrada con el servidor\n")

                    informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

                    flash('Ingreso DENEGADO hoy no tiene autorizacion para ingresar', 'warning') # info  success warning
                    info = 'Ingreso DENEGADO hoy no tiene autorizacion para ingresar'
                    print ("\n Ingreso DENEGADO hoy no tiene autorizacion para ingresar \n")

        if verificacion_serial is False:

            serial_denegado = pd.DataFrame({'SERIAL':[cod_serial]})
            cual_lab_rasdf = pd.DataFrame({'LABORATORIO':[cual_lab_ras]})
            estado_df_denegado = pd.DataFrame({'ESTADO':['Denegado serial no autorizado']})
            fecha_registro_df_denegado = pd.DataFrame({'FECHA':[fecha_registro]})
            espacio_df_d = pd.DataFrame({'':['']})

            informacion_denegado_historial = pd.concat([espacio_df_d,espacio_df_d,serial_denegado,espacio_df_d,cual_lab_rasdf,estado_df_denegado,fecha_registro_df_denegado], axis=1)

            try:
                client_ser = socket.socket()
                client_ser.connect((ip_cliente,puerto_cliente))
                print('\nConectado con el servidor')

            except:
                flash('Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente', 'warning') # info  success warning
                info = 'Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente'
                print ("\n Ingreso DENEGADO no se pudo establecer conexion con el cliente-servidor, intente nuevamente \n")
                return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

            peticion_serv = client_ser.recv(1024)
            print(peticion_serv.decode("utf-8") )
            print('Peticion recibida')
            estado_client = b"D3N3G4D0entradaFASTPEL"
            client_ser.send(estado_client)
            print("Respuesta enviada satisfactoriamente")
            client_ser.close()
            print("Conexión cerrada con el servidor\n")

            informacion_denegado_historial.reset_index(drop = True).to_csv('../data/Historial control laboratorio.csv',header=False, index=False, mode='a')

            flash('Ingreso DENEGADO, usted no esta autorizado para el ingreso', 'warning') # info  success warning
            info = 'Ingreso DENEGADO, usted no esta autorizado para el ingreso'
            print ("\n Ingreso DENEGADO, usted no esta autorizado para el ingreso \n")

            return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

        return render_template("Controllaboratorio.html", title='Control laboratorio', info=info)

    return render_template("Controllaboratorio.html", title='Control laboratorio')

# --------------------------------------------------------------------------------------------------------------------
#                                            Fin FASTPEL
# --------------------------------------------------------------------------------------------------------------------

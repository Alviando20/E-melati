from pymongo import MongoClient
import pymongo
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"

SECRET_KEY = "SPARTA"


@app.route("/", methods=['GET'])
def home():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )
        user_info = db.users.find_one({'username': payload.get('id')})
        if user_info.get('is_admin', False):
            return redirect(url_for("admin"))
        else:
            return render_template("homepage.html", user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was a problem logging you in"))

@app.route("/admin")
def admin():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )
        user_info = db.users.find_one({'username': payload.get('id')})
        if user_info.get('is_admin', False):
            return render_template("admin.html", user_info=user_info)
        else:
            return redirect(url_for("home"))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was a problem logging you in"))

@app.route("/login")
def login():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)

@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )

    if result:
        if result.get("is_admin", False):
            # Jika akun adalah admin
            payload = {
                "id": username_receive,
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify(
                {
                    "result": "success",
                    "token": token,
                    "is_admin": True,
                }
            )
        else:
            # Jika akun bukan admin
            payload = {
                "id": username_receive,
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify(
                {
                    "result": "success",
                    "token": token,
                    "is_admin": False,
                }
            )
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )

@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "username": username_receive,                               # id
        "password": password_hash,                                  # password
        "profile_name": username_receive,                           # user's name is set to their id by default
        "profile_pic": "",                                          # profile image file name
        "profile_pic_real": "profile_pics/profile_placeholder.png", # a default profile image
        "profile_info": "",                                         # a profile description
        "is_admin": False                                           # is_admin flag (default: False)
    }
    db.users.insert_one(doc)
    return jsonify({"result": "success"})

@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.user.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/jenisclient')
def jenisclient():
    return render_template('jenis_pelayanan.html')


@app.route("/konsultasi", methods=["POST"])
def pesan_post():
    nama_receive = request.form['nama_give']
    handphone_receive = request.form['handphone_give']
    pesan_receive = request.form['pesan_give']

    doc = {
        'nama': nama_receive,
        'handphone': handphone_receive,
        'pesan': pesan_receive,
    }

    db.rumah.insert_one(doc)

    return jsonify({'msg':'POST request!'})


@app.route("/konsultasi", methods=["GET"])
def pesan_get():
    pesan_list = list(db.rumah.find({},{'_id':False}))
    return jsonify({'massages':pesan_list})

@app.route("/respon")
def respon():
    return render_template('respon.html')

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        nama_pasien = request.form['nama_pasien']
        jenis_kelamin = request.form['jenis_kelamin']
        usia = request.form['usia']
        alamat = request.form['alamat']
        nomor_hp = request.form['nomor_hp']
        jenis_pelayanan = request.form['jenis_pelayanan']
        waktu_pelayanan = request.form['waktu_pelayanan']
        
        existing_user = db.data.find_one({'nama_pasien': nama_pasien})
        if existing_user:
            return '''
                <script>
                    alert("Akun sudah terdaftar silakan selesaikan terlebih dahulu pelayanannya atau hapus jadwal berobat yang sudah ada");
                    window.location.href = '/registration_data';
                </script>
            '''
            
        # Simpan data pendaftaran ke database
        db.data.insert_one({
            'nama_pasien': nama_pasien,
            'jenis_kelamin': jenis_kelamin,
            'usia': usia,
            'alamat': alamat,
            'nomor_hp': nomor_hp,
            'jenis_pelayanan': jenis_pelayanan,
            'waktu_pelayanan': waktu_pelayanan,
        })

        # Ambil data pendaftaran yang baru saja disimpan
        data = db.data.find_one({
            'nama_pasien': nama_pasien,
            'jenis_kelamin': jenis_kelamin,
            'usia': usia,
            'alamat': alamat,
            'nomor_hp': nomor_hp,
            'jenis_pelayanan': jenis_pelayanan,
            'waktu_pelayanan': waktu_pelayanan,
        })

        # Tampilkan halaman yang berisikan data pendaftaran
        return render_template('registration_data.html', data=data)

    # Ambil semua data jenis pelayanan dari database
    jenis = db.jenis.find()
    jenis_pelayanan = [jenis_data['jenis_pelayanan'] for jenis_data in jenis]

    return render_template('registration.html', jenis_pelayanan=jenis_pelayanan)


@app.route('/registration_data')
def registration_data():
    # Ambil data terbaru dari database
    data = db.data.find_one(sort=[('_id', pymongo.DESCENDING)])

    return render_template('registration_data.html', data=data)

@app.route('/index')
def index():
    data = db.data.find()
    return render_template('index.html', data=data)

@app.route('/edit/<string:nama_pasien>', methods=['GET', 'POST'])
def edit(nama_pasien):
    if request.method == 'POST':
        new_nama_pasien = request.form['nama_pasien']
        new_jenis_kelamin = request.form['jenis_kelamin']
        new_usia = request.form['usia']
        new_alamat = request.form['alamat']
        new_nomor_hp = request.form['nomor_hp']
        new_jenis_pelayanan = request.form['jenis_pelayanan']
        new_waktu_pelayanan = request.form['waktu_pelayanan']

        db.data.update_one({'nama_pasien': nama_pasien}, {"$set": {
            'nama_pasien': new_nama_pasien,
            'jenis_kelamin': new_jenis_kelamin,
            'usia': new_usia,
            'alamat': new_alamat,
            'nomor_hp': new_nomor_hp,
            'jenis_pelayanan': new_jenis_pelayanan,
            'waktu_pelayanan': new_waktu_pelayanan,
        }})

        return redirect('/index')

    data = db.data.find_one({'nama_pasien': nama_pasien})
    jenis_data = db.jenis.find()
    return render_template('edit.html', data=data, jenis=jenis_data)

@app.route('/delete/<string:nama_pasien>', methods=['GET', 'POST'])
def delete(nama_pasien):
    db.data.delete_one({'nama_pasien': nama_pasien})
    return redirect('/index')

@app.route('/jenis', methods=['GET', 'POST'])
def jenis():
    if request.method == 'POST':
        jenis_pelayanan = request.form['jenis_pelayanan']
        
        # Simpan data pendaftaran ke database
        db.jenis.insert_one({
            'jenis_pelayanan': jenis_pelayanan,
        })
    
    # Ambil semua data pendaftaran yang ada di database
    jenis_data = db.jenis.find()

    return render_template('upjenis.html', jenis=jenis_data)

@app.route('/indexjenis')
def indexjenis():
    jenis = db.jenis.find()
    return render_template('upjenis.html', jenis=jenis)

@app.route('/add_jenis', methods=['POST'])
def add_jenis():
    jenis_pelayanan = request.form['jenis_pelayanan']
    
    # Simpan data pendaftaran ke database
    db.jenis.insert_one({
        'jenis_pelayanan': jenis_pelayanan,
    })

    # Ambil semua data pendaftaran yang ada di database
    jenis_data = db.jenis.find()

    return render_template('upjenis.html', jenis=jenis_data)


# @app.route('/delete_jenis', methods=['POST'])
# def delete_jenis():
#     jenis_pelayanan = request.form['jenis_pelayanan']
#     # Hapus data pelayanan dari database
#     db.jenis.delete_one({
#         'jenis_pelayanan': jenis_pelayanan,
#     })
#     # Redirect ke halaman utama setelah menghapus data
#     return redirect('/add_jenis')

@app.route('/delete_jenis/<string:jenis_pelayanan>', methods=['GET', 'POST'])
def delete_jenis(jenis_pelayanan):
    db.jenis.delete_one({'jenis_pelayanan': jenis_pelayanan})
    return redirect('/indexjenis')

# @app.route('/jenis')
# def jenis():
#     jenis_pelayanan = list(db.jenis.find({}, {'_id': False}))
#     return render_template('upjenis.html', jenis_pelayanan=jenis_pelayanan)

# @app.route("/add_jenis", methods=["POST"])
# def add_jenis():
#     new_jenis = request.form["new_jenis"]
#     db.jenis.insert_one({"jenis_pelayanan": new_jenis})
#     return redirect(url_for("jenis"))

# @app.route("/delete_jenis", methods=["POST"])
# def delete_jenis():
#     jenis_pelayanan = request.form["jenis_pelayanan"]
#     db.jenis.delete_one({"jenis_pelayanan": jenis_pelayanan})
#     return redirect(url_for("jenis"))

# buat konsulclient

@app.route('/konsulclient', methods=['GET', 'POST'])
def konsulclient():
    if request.method == 'POST':
        nama_pasien = request.form['nama_pasien']
        jenis_kelamin = request.form['jenis_kelamin']
        usia = request.form['usia']
        keluhan = request.form['keluhan']
        nomor_hp = request.form['nomor_hp']
        
        # Simpan data pendaftaran ke database
        db.konsul.insert_one({
            'nama_pasien': nama_pasien,
            'jenis_kelamin': jenis_kelamin,
            'usia': usia,
            'keluhan': keluhan,
            'nomor_hp': nomor_hp,
        })

        # Kembali ke halaman homepage
        return redirect(url_for('home'))

    return render_template('konsultasi.html')

@app.route('/admin_respon')
def adminrespon():
    konsul = db.konsul.find()
    return render_template('admin_respon.html', konsul=konsul)

@app.route('/deletekonsul/<string:nama_pasien>', methods=['GET', 'POST'])
def deletekonsul(nama_pasien):
    db.konsul.delete_one({'nama_pasien': nama_pasien})
    return redirect('/admin_respon')



@app.route('/edit_tampilan')
def edit_tampilan():
    return render_template('edit_tampilan.html')

@app.route('/tampilan')
def tampilan():
    return render_template('tampilan.html')

@app.route('/tampilandiary', methods=['GET'])
def tampilandiary():
    # sample_receive = request.args.get('sample_give')
    # print(sample_receive)

    articles = list(db.diary.find({}, {'_id': False}))
    return jsonify({'articles': articles})

@app.route('/diary', methods=['GET'])
def show_diary():
    # sample_receive = request.args.get('sample_give')
    # print(sample_receive)

    articles = list(db.diary.find({}, {'_id': False}))
    return jsonify({'articles': articles})

@app.route('/diary', methods=['POST'])
def save_diary():
    title_receive = request.form.get('title_give')
    content_receive = request.form.get('content_give')

    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    file = request.files["file_give"]
    extension = file.filename.split('.')[-1]
    filename = f'static/post-{mytime}.{extension}'
    file.save(filename)

    time = today.strftime('%Y.%m.%d')

    doc = {
        'file': filename,
        'title':title_receive,
        'content':content_receive,
        'time':time,
    }
    db.diary.insert_one(doc)

    return jsonify({'msg':'Upload complete!'})

@app.route('/diary/<title>', methods=['DELETE'])
def delete_diary(title):
    db.diary.delete_one({'title': title})
    return jsonify({'msg': 'Article deleted!'})



if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)

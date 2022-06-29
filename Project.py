from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import timedelta, date, datetime
import os
from werkzeug.utils import secure_filename

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
current_date = now.strftime("%y-%m-%d")

app = Flask(__name__)
app.secret_key = "ssss"           # to use flash  we set a app secret key 
                               
app.config["MYSQL_HOST"] = 'localhost'        # connecting to the database
app.config["MYSQL_USER"] = 'root'
app.config["MYSQL_PASSWORD"] = '7117755.'
app.config["MYSQL_DB"] = 'final'
mysql = MySQL(app)

path_files = "css_file" 
path = "static"                                       # just give the path to a specific css file
app.config["UPLOAD_FOLDER"] = path

path_of_style = os.path.join(path, "style.css")       # just for the dashboard design

# ****************************   Index page loading ******************************************  

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        user_data = request.form
        user_First_name = user_data['First-Name']
        user_Last_name = user_data['Last-Name']
        user_email = user_data['email']
        user_password = user_data["Password"]
        user_phone = user_data['Phone Numer']
        user_name = user_data['user-name']
        file = request.files['user-img']         #   use a file variable 

        file_name = file.filename
        file_name = secure_filename(file_name)     
        file.save(os.path.join(path, file_name))

        image = os.path.join(path, file_name)      # read the image from the folder 
        with open(image, 'rb') as file:             # use rb to read the image 
            binaryData = file.read()                # saving binary values in the binary data variable

        #          ------ saving data in database  ----------------

        cur = mysql.connection.cursor()            # make the pointer so we apply the database opertaions
        cur.execute('select * from user_data where User_name=%s', [user_name])   # check users exist or not
        result = cur.fetchall() 

        #       ---    check wether the username exists  if  exists we remain on the same page  ---
        if len(result) != 0:
            flash("user name is already taken")
            redirect(url_for('index'))
            
        #       ---    check wether the username exists  if  do not exists parts
        #              then save the data of new user and take it to the login page  ---   
        else:
            print("dddd")
            cur.execute('insert into user_data(id,F_name,L_name,User_name,email,pasw,phone_num,image) \
            values (NULL,%s,%s,%s,%s,%s,%s,%s)',
                        (user_First_name, user_Last_name, user_name, user_email, user_password, user_phone, binaryData))
            cur.connection.commit()
            cur.close()
            os.remove(image)
            return redirect("/3rd")
        
        
    return render_template('projIndex.html', path=os.path.join(path, "index.css"), message="")

# ****************************   Login page loading ****************************************** 

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        login_data = request.form
        name = login_data["User-Name"]
        password = login_data["Password"]
        cur = mysql.connection.cursor()
        cur.execute("select * from user_data where User_Name=%s and pasw = %s", (name, password))
        user = cur.fetchall()
        
          # -----  check the correct login --------
        if len(user) != 0:
            cur.execute("select id,image from user_data where User_Name=%s", [name])
            result = cur.fetchone()
            print(len(result))
            # id = result[0]
            
            #  Read  the image so we can send it to dashboard display
            image = result[1]
            filepath = os.path.join(path, (name + '.png'))
            with open(filepath, 'wb') as file:
                file.write(image)

            return redirect(url_for('dashboard', name=name, image=filepath))

    return render_template('login.html', )


# ****************************  Dashboard  loading ****************************************** 

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    name = request.args.get("name")      # getting arguments which were passed during loginl
    image = request.args.get("image")
    posts = []
    
    #                              ---------------    if user wants to tweet -----------------------
    
    if request.method == "POST":
        tweet_data = request.form
        text_ = tweet_data["text_"]
        photo = request.files["img"]

        # ..........................             checking while tweet is empty?       ...............................

        if len(text_) < 1 and photo.filename == '':
            print("empty tweet")
            
        # if tweet is not empty then the user data of tweet is fatched
        else:
            cur = mysql.connection.cursor()
            cur.execute("select F_name,image from user_data where User_Name=%s", [name])
            result = cur.fetchone()
            f_name = result[0]
            user_img = result[1]
            print(user_img)

            # This part is used to check that wheather the tweet has any image or not 
            if photo.filename == '':
                binaryData = None             
            else:
                file_name = photo.filename
                file_name = secure_filename(file_name)
                photo.save(os.path.join(path, file_name))
                image1 = os.path.join(path, file_name)
                with open(image1, 'rb') as file:
                    binaryData = file.read()
            
            # this is used to insert data of the new posts into the post table
            cur.execute('insert into post(post_id,user_img,F_name,user_name,text_,img,date_,time_)\
                        values(NULL,%s,%s,%s,%s,%s,%s,%s)', (user_img, f_name, name, text_, binaryData, current_date,
                                                             current_time))
            cur.connection.commit()
            cur.close()

            return redirect(url_for('dashboard1', name=name, image=image))    
        
        # we will again return to the dashboard after the user do new tweat

        # deshboard without new post

    else:                                                                            
        cur = mysql.connection.cursor()
        cur.execute('select * from post order by date_ desc,time_ DESC')
        lists = cur.fetchall()

        for i in lists:
            filepath = os.path.join(path, (str(i[0]) + i[3] + '.png'))
            with open(filepath, 'wb') as file:
                file.write(i[1]) 

            user_img = filepath                # checking image if present  
            if i[5] is None:
                post_img = None
            else:
                filepath = os.path.join(path, (i[3] + str(i[0]) + '.png'))
                with open(filepath, 'wb') as file:
                    file.write(i[5])
                post_img = filepath
                
            posts.append((i[0], user_img, i[2], i[3], i[4], post_img, i[6], i[7]))

    return render_template('dashboard1.html', path_of_style=path_of_style, image=image, len=len(posts), name=name,
                           posts=posts)

# @app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(seconds=100)
    
# ****************************  Profile loading ******************************************   

@app.route("/profile", methods=['GET', 'POST'])
def profile():
    name = request.args.get('name')
    image = request.args.get('image')
    print(name)
    cur = mysql.connection.cursor()
    cur.execute("select * from user_data where User_name = %s", [name])
    profiles = cur.fetchone()
    print(profiles[1])
    user_photo = profiles[7]
    filepath = os.path.join(path, (name + '.png'))
    with open(filepath, 'wb') as file:
        file.write(user_photo)

    list_of_profile = [profiles[1], profiles[2], profiles[4], profiles[5], profiles[6], filepath]
    print(list_of_profile)
    return render_template("profile.html", path=os.path.join(path, "profile.css"), image=image, name=name,
                           list=list_of_profile)
# ****************************   Friend  loading ****************************************** 
@app.route('/friend')
def friend():
    name = request.args.get('name')
    f_name = request.args.get('f_name')
    image = request.args.get('image')

    cur = mysql.connection.cursor()
    cur.execute('select * from friends where (user_name=%s and friend_name=%s)', (name, f_name))
    result = cur.fetchall()
    print(len(result))
    if len(result) != 0:
        cur.execute("delete from friends where( user_name=%s and friend_name=%s)", (name, f_name))
        cur.connection.commit()
        cur.close()
    else:
        cur.execute("select F_name,L_name,image from user_data where User_Name = %s", [f_name])
        result = cur.fetchone()
        cur.execute("insert into friends(id,user_name,friend_name,pic,F_name,L_name) values(NULL,%s,%s,%s,%s,%s)",
                    (name, f_name, result[2], result[0], result[1]))
        cur.connection.commit()
        cur.close()
    return redirect(url_for('dashboard', name=name, image=image))

# ****************************  Following  loading ****************************************** 

@app.route('/followings')
def followings():
    name = request.args.get('name')
    image = request.args.get('image')
    followers = []
    cur = mysql.connection.cursor()
    cur.execute('select * from friends where user_name=%s', [name])
    result = cur.fetchall()

    for i in result:
        filepath = os.path.join(path, (i[2] + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[3])
        user_img = filepath

        followers.append((user_img, i[4], i[5], i[2]))
    print(followers)
    return render_template('friends.html', name=name, path_of_style1=os.path.join(path, 'friends.css'), image=image,
                           len=len(followers),
                           list=followers)


# ****************************  loading ****************************************** 

@app.route("/ids")
def follower_ids():
    name = request.args.get("name")
    image = request.args.get("image")
    follower_id = request.args.get('id_')
    posts1 = []
    cur = mysql.connection.cursor()
    cur.execute('select F_name,L_name,image from user_data where user_name=%s', [follower_id])
    result = cur.fetchone()

    filepath = os.path.join(path, (follower_id + '.png'))
    with open(filepath, 'wb') as file:
        file.write(result[2])

    friend_img = filepath

    list_of_userID = (result[0], result[1], friend_img, follower_id)
    cur.execute('select * from post where user_name = %s order by date_ desc,time_ DESC', [follower_id])
    lists = cur.fetchall()

    for i in lists:
        filepath = os.path.join(path, (str(i[0]) + i[3] + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[1])

        user_img = filepath

        filepath = os.path.join(path, (i[3] + str(i[0]) + '.png'))
        with open(filepath, 'wb') as file:
            file.write(i[5])
        post_img = filepath
        posts1.append((i[0], user_img, i[2], i[3], i[4], post_img, i[6], i[7]))

    return render_template('T_dashboard.html', style=os.path.join(path_files, 'friend_id.css'), image=image, len=len(posts1),
                           name=name,
                           posts=posts1,
                           list=list_of_userID)

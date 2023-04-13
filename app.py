from flask import Flask , render_template,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Float
from datetime import datetime
from flask_wtf import Form
from wtforms import DateField
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from dotenv import load_dotenv
import os
import multiprocessing


app = Flask(__name__)
load_dotenv()


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///water_quality_parameters.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)

class water_quality_parameters(db.Model):
    sno=db.Column(db.Integer,primary_key=True)
    TDS=db.Column(db.Float(precision=3),nullable=False)
    TEMP=db.Column(db.Float(precision=2),nullable=False)
    PH_value=db.Column(db.Float(precision=2),nullable=False)
    date=db.Column(db.DateTime,default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.TDS} - {self.TEMP} - {self.PH_value}"

        
def last_recored_data():
    connect=sqlite3.connect('water_quality_parameters.db')
    c=connect.cursor()
    last=[]
    for row in c.execute("SELECT * FROM water_quality_parameters ORDER BY date DESC LIMIT 1"):
        last.append(row[1])
        last.append(row[2])
        last.append(row[3])

    return last

def send_email(subject, message):
    # Replace the placeholders with your own email and password
    import os
    email = "ankurwatersolu@gmail.com"
    password = os.getenv('EMAIL_PASSWORD')

    # Create a message object and set the message and subject
    msg = EmailMessage()
    msg['From'] = email
    msg['To'] = ['cs20b1098@iiitdm.ac.in','ec20b1059@iiitdm.ac.in']
    msg['Subject'] = subject
    msg.set_content(MIMEText(message, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email,password)
        smtp.send_message(msg)
        print("Email sent successfully !!")


@app.route('/data', methods=['POST'])
def receive_data():
     # Get data from request
    data_str = request.data.decode('utf-8')
    data = data_str.split(',')

    # Store data in the database
    tds = float(data[1])
    temp = float(data[0])
    ph = float(data[2])
    salinity= float(tds/0.55)

    # Check if TDS, pH or temperature values exceed a certain threshold
    subject = "Water quality alert"
    message = f"TDS: {tds}\nTemperature: {temp}\npH: {ph}\nSalinity :{salinity}"
    flag=False
    if(ph<6.5):
        m="\nWater showing Acidic behaviour, do not consume"
        message+=m
        flag=True
    elif(ph>8):
        m="\nWater showing Alkaline behaviour, do not consume"
        message+=m
        flag=True
    elif(ph>7 and ph<8 ):
        m="\nWater showing slightly Alkaline behaviour check for other constituents as this kind of water be sometimes good for health"
        message+=m
        if(temp<27):
            if(tds<150):
                m="\nExcellent for Drinking"
                message+=m
            elif(tds<250):
                m="\nVery slight impurities still drinkable"
                message+=m
                flag=True
            elif(tds<300):
                m="\nImpurities present if Possible perform filteration "
                message+=m
                flag=True
            elif(tds<500):
                m="\nDo not Consume without filteration ,But can we used for gardening and washing purposes"
                message+=m
                flag=True
            else:
                m="\nNot safe for drinking"
                message+=m
                flag=True
        else:
            flag=True
            if(tds<250):
                m="\nPossibiltty of bacterial growth, do not consume without boiling or other bacteria removal treatment"
                message+=m
            else:
                m="\nNot safe for drinking as temp and tds parameters are not favourable"
                message+=m
    if flag:    
        send_email(subject, message)

    measurements = water_quality_parameters(TDS=tds, TEMP=temp, PH_value=ph)
    db.session.add(measurements)
    db.session.commit()

    # Send response
    response = {'status': 'Success'}
    return jsonify(response)


@app.route('/',methods=['GET','POST'])
def display():
    if request.method=='POST':
        tds=request.form['tds_data']
        temp=request.form['temp_data']
        ph=request.form['ph_data']
    
        measurements=water_quality_parameters(TDS=tds,TEMP=temp,PH_value=ph)
        db.session.add(measurements)
        db.session.commit()

    stored_data=water_quality_parameters.query.all()
    tds_val=[data.TDS for data in stored_data]
    temp_val=[data.TEMP for data in stored_data]
    ph_val=[data.PH_value for data in stored_data]

    connect=sqlite3.connect('water_quality_parameters.db')
    c=connect.cursor()
    # d=[]
    # for row in c.execute("SELECT * FROM water_quality_parameters WHERE date >= '2023-03-07'"):
    #     d.append(row[0])

    # print(d)
    curr=last_recored_data()
    return render_template("index.html",stored_data=stored_data,curr=curr,graph_tds=tds_val,graph_temp=temp_val,graph_ph=ph_val )

@app.route('/vision')
def member():
    return render_template("about.html")

@app.route('/team')
def me():
    return render_template("team.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,port=8080)
    # workers = multiprocessing.cpu_count() * 2 + 1
    # bind = "0.0.0.0:8080"
    # worker_class = "gevent"
    # timeout = 120

    # print("Starting Gunicorn...")
    # print(f"Workers: {workers}")
    # print(f"Bind: {bind}")
    # print(f"Worker Class: {worker_class}")
    # print(f"Timeout: {timeout}")

    # # Start Gunicorn server
    # try:
    #     from gunicorn import version_info as gunicorn_version_info
    #     if gunicorn_version_info >= (20, 0):
    #         # New API in Gunicorn 20+
    #         from gunicorn.config import Config
    #         config = Config()
    #         config.set("workers", workers)
    #         config.set("bind", bind)
    #         config.set("worker_class", worker_class)
    #         config.set("timeout", timeout)
    #         from gunicorn.app.wsgiapp import WSGIApplication
    #         WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]").run()
    #     else:
    #         # Old API in Gunicorn 19.x and lower
    #         from gunicorn.app.base import Application
    #         class FlaskApplication(Application):
    #             def init(self, parser, opts, args):
    #                 return {
    #                     "bind": bind,
    #                     "workers": workers,
    #                     "worker_class": worker_class,
    #                     "timeout": timeout,
    #                 }

    #             def load(self):
    #                 return app

    #         FlaskApplication().run()
    # except ImportError:
    #     print("Gunicorn is not installed.")

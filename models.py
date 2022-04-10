# create the application object
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import BaseConfig

app = Flask(__name__)
# set database name
app.database = "agents.db"
# load the config
app.config.from_object(BaseConfig)
# create the sqlalchemy object
db = SQLAlchemy(app)


class Agent(db.Model):
    __tablename__ = "AGENTS"
    id = db.Column(db.Integer, primary_key=True)
    os = db.Column(db.String, nullable=False)
    host_name = db.Column(db.String, nullable=True)
    ip = db.Column(db.String, nullable=True)
    ram = db.Column(db.String, nullable=True)

    def __init__(self, os, host_name, ip, ram):
        self.os = os
        self.host_name = host_name
        self.ip = ip
        self.ram = ram

    def __repr__(self):
        return f"os: {self.os}, host_name: {self.host_name}, ip: {self.ip}, ram: {self.ram}, id: {self.id}"


class CommandQueue(db.Model):
    __tablename__ = "COMMAND QUEUE"
    id = db.Column(db.String, primary_key=True)
    command = db.Column(db.String, nullable=True)
    output = db.Column(db.String, nullable=True)

    def __init__(self, id, command=None, output=None):
        self.id = id
        self.command = command
        self.output = output

    def __repr__(self):
        return f"id: {self.id}, command: {self.command}, output: {self.output}"

# Importacion de las librerias necesarias
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import pyodbc
import mysql.connector
import uuid
import time
import os
from datetime import datetime, timedelta

# Aqui creamos la aplicacion usando el Framework Flask
app = Flask(__name__)
app.secret_key = "root123"

SQL_SERVER_CONFIG = {
    "driver": "{ODBC Driver 17 for SQL Server}",
    "server": "localhost",
    "database": "BD_Okami",
    "timeout": 3,
}
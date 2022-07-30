#!/bin/bash

#python3 app.py
gunicorn -b 0.0.0.0:5000 app:app

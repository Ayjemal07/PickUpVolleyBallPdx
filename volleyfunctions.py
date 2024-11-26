#This file contains routes/blueprints

from flask import Blueprint, jsonify, render_template, session, request
from flask_login import current_user  # Import current_user here
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os
# from .models import Activity



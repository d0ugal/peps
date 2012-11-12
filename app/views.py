from flask import Blueprint, render_template


mod = Blueprint('base', __name__)


@mod.route('/')
def index():

    return render_template('base/index.html')

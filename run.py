"""Development entry point — run from project root: python run.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.app import app as dash_app
from app.app import CFG

if __name__ == "__main__":
    dash_app.run(debug=True, host="0.0.0.0", port=CFG["app"]["port"])

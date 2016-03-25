import sys
import os

sys.stdout = sys.stderr
sys.path.append(os.path.dirname(__file__))

from webjuggler import app as application

from app import app, db
from app.models import User, Home, Device, Category, DataPoint

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Home': Home, 'Device': Device, 'Category': Category, 'DataPoint': DataPoint}
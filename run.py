from app import app
from flask_socketio import SocketIO
import eventlet

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

# Register socketio events from routes.py
from app import routes
routes.register_socketio_events(socketio)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5050)

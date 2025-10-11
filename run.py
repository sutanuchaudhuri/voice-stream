from app import app, socketio
from app.routes import register_socketio_events
import os

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('annotation_workspaces', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)

    # Register socket events
    register_socketio_events(socketio)

    # Run the app
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)

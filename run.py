from app import app, socketio
import os

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('annotation_workspaces', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)

    # Run the app
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)

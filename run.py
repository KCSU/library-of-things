"""Application entry point"""

import os
from app import create_app

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8765)
"""Entry point for running the Flask dashboard."""

from dashboard import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Banking System Dashboard")
    print("📱 Navigate to: http://localhost:5000/dashboard/")
    app.run(debug=True, host='0.0.0.0', port=5000)

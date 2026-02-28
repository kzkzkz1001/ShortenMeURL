✨ Key Features
Efficient Shortening: Converts long URLs into unique 6-character short codes.

High-Performance Redirection:

Caching Strategy: Integrates Redis as a caching layer, prioritizing memory-based lookups to significantly reduce database load.

Cache-Aside Pattern: Implements automatic cache population; if a cache miss occurs, the service retrieves the data from MySQL and backfills the cache for subsequent requests.

Enterprise-Grade Reliability:

Global Error Handling: Utilizes custom errorhandler functions to catch 400, 404, and 500 exceptions, returning standardized JSON responses.

Robust Logging: Includes a configured logging system to track incoming requests and system health in real-time.

Data Persistence: Uses Flask-SQLAlchemy for ORM-based interactions with MySQL to ensure data integrity.

🛠 Tech Stack
Framework: Flask

Database: MySQL (via SQLAlchemy)

Cache: Redis

Logging: Python Logging module

⚙️ Getting Started
Environment Setup:
Ensure you have the necessary dependencies installed:

Bash
pip install flask flask-sqlalchemy pymysql redis
Infrastructure:

Ensure your MySQL server is running and update the database URI in the configuration.

Ensure a Redis instance is running on the default port 6379.

Running the App:

Bash
python app.py

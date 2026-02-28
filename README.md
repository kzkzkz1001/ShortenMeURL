# 🚀 URL Shortener Service

## ✨ Key Features
* **Efficient Shortening**: Converts long URLs into unique 6-character short codes.
* **High-Performance Redirection**:
    * **Caching Strategy**: Integrates Redis as a caching layer.
    * **Cache-Aside Pattern**: Implements automatic cache population.

## 🛠 Tech Stack
* **Framework**: Flask
* **Database**: MySQL
* **Cache**: Redis

## ⚙️ Getting Started
### Environment Setup
```bash
pip install flask flask-sqlalchemy pymysql redis

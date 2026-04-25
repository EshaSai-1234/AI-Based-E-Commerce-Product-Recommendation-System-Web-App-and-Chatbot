# AI-Based E-Commerce Product Recommendation System

A modern, full-stack e-commerce recommendation system powered by **FastAPI** on the backend and **Streamlit** on the frontend. The system includes an intelligent AI chatbot for product discovery and data-driven recommendations.

## 🚀 Features

-   **Intelligent Chatbot**: Powered by OpenAI, the chatbot helps users find products based on their preferences and queries.
-   **Product Recommendations**: Advanced recommendation engine utilizing product data to suggest relevant items.
-   **Interactive Frontend**: A sleek and responsive user interface built with Streamlit for a premium user experience.
-   **FastAPI Backend**: High-performance asynchronous API service for handling data processing and AI logic.
-   **Docker Ready**: Each component comes with its own Dockerfile for easy deployment and containerization.

## 🛠️ Tech Stack

-   **Backend**: FastAPI, Python, OpenAI API, Pandas, Scikit-learn.
-   **Frontend**: Streamlit, Custom CSS.
-   **Data Analysis**: Pandas for processing product datasets.
-   **Deployment**: Docker.

## 📋 Prerequisites

-   Python 3.8+
-   An OpenAI API Key (for the chatbot functionality)

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Ecommerce-Product-Recommendation-System.git
cd Ecommerce-Product-Recommendation-System
```

### 2. Backend Setup
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure environment variables:
    -   Rename `.env.example` to `.env`.
    -   Add your `MY_OPENAI_KEY` in the `.env` file.

### 3. Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Running the Application

You can use the provided `run_app.py` script to launch both the backend and frontend simultaneously:

```bash
python run_app.py
```

-   **Backend** will run on: `http://localhost:8000`
-   **Frontend** will run on: `http://localhost:8501`

## 📁 Project Structure

```text
├── backend/
│   ├── app.py             # FastAPI entry point
│   ├── chatbot.py         # AI Logic
│   ├── dockerfile         # Backend container config
│   ├── requirements.txt   # Backend dependencies
│   └── .env               # Environment variables (Private)
├── frontend/
│   ├── app.py             # Streamlit application
│   ├── dockerfile         # Frontend container config
│   └── requirements.txt   # Frontend dependencies
├── amazon.csv              # Product Dataset
├── run_app.py              # Orchestration script
└── .gitignore              # Files to exclude from Git
```

---
*Created for modern E-commerce experiences.*

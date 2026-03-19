# AI-Powered Traveller Recommendation and Smart Trip Planner

A full-featured Flask web application with ML-based destination recommendations, itinerary planning, and an interactive travel dashboard.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### Core Functionality
- **User Authentication** - Secure login/registration with Flask-Login
- **ML-Powered Recommendations** - K-Nearest Neighbors algorithm for personalized destination suggestions
- **Interactive Dashboard** - Track saved destinations and planned trips
- **Itinerary Builder** - Create and manage day-by-day travel plans
- **Destination Gallery** - Visual exploration of travel destinations
- **Interactive Maps** - Location-based destination exploration with coordinates

### Recommendation Engine
- Uses **scikit-learn** for machine learning
- KNN-based collaborative filtering
- Considers destination type, budget, travel style, and season
- Match scoring system for better recommendations

### Destination Database
- 25+ destinations including:
  - International: Tokyo, Kyoto, Bali, Rome, New York, Swiss Alps
  - Indian: Goa, Manali, Ladakh, Rishikesh, Mysore, Bangalore, Nandi Hills
  - Local Karnataka: Muddenhalli, Chikkaballapur

## 📋 Requirements

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.1
SQLAlchemy==2.0.23
scikit-learn==1.3.2
numpy==1.26.2
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   cd travellar-web
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

## 📁 Project Structure

```
travellar-web/
├── app.py                 # Main Flask application with ML engine
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── static/
│   ├── css/
│   │   └── style.css     # Styling for all pages
│   ├── images/           # Static images
│   └── js/
│       └── main.js       # Client-side JavaScript
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Home/Landing page
    ├── login.html        # User login
    ├── register.html     # User registration
    ├── dashboard.html    # User dashboard
    ├── preferences.html  # Travel preferences
    ├── recommendations.html # ML recommendations
    ├── destination.html  # Destination details
    ├── gallery.html      # Photo gallery
    └── map.html          # Interactive map
```

## 🎯 Usage

### For Users
1. **Register** - Create an account with username, email, and password
2. **Set Preferences** - Choose destination type, budget, travel days, travel style, and season
3. **Get Recommendations** - View AI-powered destination suggestions
4. **Explore Destinations** - View detailed info, gallery, and map
5. **Plan Trips** - Create itineraries with daily activities

### Pages Overview

| Page | Description |
|------|-------------|
| `index.html` | Landing page with featured destinations |
| `login.html` | User authentication |
| `register.html` | New user registration |
| `dashboard.html` | User's saved destinations and itineraries |
| `preferences.html` | Set travel preferences for recommendations |
| `recommendations.html` | ML-generated destination suggestions |
| `destination.html` | Detailed view of a single destination |
| `gallery.html` | Visual gallery of destinations |
| `map.html` | Geographic map of destinations |

## 🔧 Configuration

### Database
The application uses SQLite (`travel_planner.db`) which is automatically created on first run.

### Secret Key
Update the secret key in `app.py` for production:
```python
app.config['SECRET_KEY'] = 'your-secure-secret-key'
```

## 🤖 Machine Learning Details

### Algorithm
- **K-Nearest Neighbors (KNN)** from scikit-learn
- Feature vector includes: destination type, budget, cost ratio, latitude, longitude
- Uses MinMaxScaler for feature normalization

### Recommendation Factors
- Destination type matching
- Budget compatibility
- Travel style alignment
- Seasonal suitability

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## 🧪 Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy
- **ML**: scikit-learn, NumPy
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Unsplash for destination images
- Flask community for the excellent framework
- scikit-learn for ML capabilities

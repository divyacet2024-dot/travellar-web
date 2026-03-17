"""
AI Powered Traveller Recommendation and Smart Trip Planner
Flask Backend Application with ML-based Recommendation Engine
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import os
from datetime import datetime
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.neighbors import NearestNeighbors
import json
import ollama

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Database setup
def init_db():
    conn = sqlite3.connect('travel_planner.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User preferences table
    c.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        destination_type TEXT,
        budget TEXT,
        travel_days INTEGER,
        travel_type TEXT,
        season TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Itineraries table
    c.execute('''CREATE TABLE IF NOT EXISTS itineraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        destination TEXT NOT NULL,
        days INTEGER,
        itinerary_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('travel_planner.db')
    c = conn.cursor()
    c.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

# Destination Database - Pre-populated travel destinations
DESTINATIONS = [
    {
        'name': 'Maldives',
        'type': 'Beach',
        'description': 'A tropical paradise with pristine beaches, crystal-clear waters, and luxury resorts. Perfect for beach lovers and honeymooners.',
        'attractions': 'Baros Island, Male City, Bikini Beach, Whale Shark Diving, Sunset Dolphin Cruise',
        'estimated_cost': 150000,
        'best_time': 'November to April',
        'latitude': 3.2028,
        'longitude': 73.2207,
        'image_url': 'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800'
    },
    {
        'name': 'Manali',
        'type': 'Hill',
        'description': 'A beautiful hill station in Himachal Pradesh surrounded by snow-capped mountains, lush green valleys, and adventure activities.',
        'attractions': 'Solang Valley, Rohtang Pass, Hadimba Temple, Beas River, Mall Road',
        'estimated_cost': 25000,
        'best_time': 'March to June, December to February',
        'latitude': 32.2396,
        'longitude': 77.1887,
        'image_url': 'https://images.unsplash.com/photo-1508193638397-1c4234db14d9?w=800'
    },
    {
        'name': 'Tokyo',
        'type': 'City',
        'description': 'A fascinating blend of ancient traditions and cutting-edge technology. Experience unique cuisine, historic temples, and vibrant nightlife.',
        'attractions': 'Senso-ji Temple, Shibuya Crossing, Tokyo Tower, Meiji Shrine, Akihabara',
        'estimated_cost': 120000,
        'best_time': 'March to May, September to November',
        'latitude': 35.6762,
        'longitude': 139.6503,
        'image_url': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800'
    },
    {
        'name': 'Rishikesh',
        'type': 'Adventure',
        'description': 'The adventure capital of India offering river rafting, bungee jumping, trekking, and yoga retreats in the Himalayas.',
        'attractions': 'River Rafting, Bungee Jumping, Lakshman Jhula, Beatles Ashram, Trekking Trails',
        'estimated_cost': 30000,
        'best_time': 'September to June',
        'latitude': 30.0869,
        'longitude': 78.2676,
        'image_url': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800'
    },
    {
        'name': 'Kyoto',
        'type': 'Cultural',
        'description': 'The cultural heart of Japan with over 2,000 temples and shrines, traditional gardens, and authentic Japanese experiences.',
        'attractions': 'Fushimi Inari Shrine, Arashiyama Bamboo Grove, Kinkaku-ji, Gion District, Philosopher\'s Path',
        'estimated_cost': 100000,
        'best_time': 'March to May, October to November',
        'latitude': 35.0116,
        'longitude': 135.7681,
        'image_url': 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800'
    },
    {
        'name': 'Goa',
        'type': 'Beach',
        'description': 'India\'s party capital with beautiful beaches, Portuguese architecture, vibrant nightlife, and delicious seafood.',
        'attractions': 'Baga Beach, Anjuna Beach, Dudhsagar Falls, Fort Aguada, Basilica of Bom Jesus',
        'estimated_cost': 35000,
        'best_time': 'October to March',
        'latitude': 15.2993,
        'longitude': 74.1240,
        'image_url': 'https://images.unsplash.com/photo-1518546979797-8494b522d09b?w=800'
    },
    {
        'name': 'Ladakh',
        'type': 'Hill',
        'description': 'A breathtaking high-altitude desert with stunning mountain landscapes, Buddhist monasteries, and thrilling adventures.',
        'attractions': 'Pangong Lake, Nubra Valley, Thiksey Monastery, Magnetic Hill, Khardung La Pass',
        'estimated_cost': 45000,
        'best_time': 'May to September',
        'latitude': 34.1526,
        'longitude': 77.5760,
        'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800'
    },
    {
        'name': 'New York City',
        'type': 'City',
        'description': 'The city that never sleeps! Experience iconic landmarks, world-class dining, Broadway shows, and diverse neighborhoods.',
        'attractions': 'Statue of Liberty, Central Park, Times Square, Empire State Building, Brooklyn Bridge',
        'estimated_cost': 200000,
        'best_time': 'April to June, September to November',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'image_url': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800'
    },
    {
        'name': 'Swiss Alps',
        'type': 'Adventure',
        'description': 'Experience world-class skiing, mountaineering, and breathtaking mountain scenery in the heart of Europe.',
        'attractions': 'Matterhorn, Jungfrau, Interlaken, Lake Geneva, Swiss Museum of Transport',
        'estimated_cost': 180000,
        'best_time': 'December to March, June to September',
        'latitude': 46.8182,
        'longitude': 8.2275,
        'image_url': 'https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800'
    },
    {
        'name': 'Rome',
        'type': 'Cultural',
        'description': 'The Eternal City with ancient ruins, Renaissance art, Vatican City, and delicious Italian cuisine.',
        'attractions': 'Colosseum, Vatican City, Trevi Fountain, Pantheon, Roman Forum',
        'estimated_cost': 90000,
        'best_time': 'April to June, September to October',
        'latitude': 41.9028,
        'longitude': 12.4964,
        'image_url': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800'
    },
    {
        'name': 'Bali',
        'type': 'Beach',
        'description': 'A tropical Indonesian paradise with stunning beaches, ancient temples, rice terraces, and vibrant culture.',
        'attractions': 'Uluwatu Temple, Tegallalang Rice Terraces, Seminyak Beach, Ubud Monkey Forest, Tanah Lot',
        'estimated_cost': 60000,
        'best_time': 'April to October',
        'latitude': -8.3405,
        'longitude': 115.0920,
        'image_url': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800'
    },
    {
        'name': 'Sikkim',
        'type': 'Hill',
        'description': 'A northeastern Indian state with pristine natural beauty, snow-capped mountains, and rich Buddhist culture.',
        'attractions': 'Lake Tsongmo, Nathula Pass, Rumtek Monastery, Gangtok, Kangchenjunga Base Camp',
        'estimated_cost': 40000,
        'best_time': 'March to June, October to December',
        'latitude': 27.5142,
        'longitude': 88.5948,
        'image_url': 'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800'
    },
    {
        'name': 'Dubai',
        'type': 'City',
        'description': 'A futuristic city with iconic skyscrapers, luxury shopping, desert safaris, and world-class entertainment.',
        'attractions': 'Burj Khalifa, Dubai Mall, Palm Jumeirah, Desert Safari, Dubai Marina',
        'estimated_cost': 80000,
        'best_time': 'November to March',
        'latitude': 25.2048,
        'longitude': 55.2708,
        'image_url': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800'
    },
    {
        'name': 'Costa Rica',
        'type': 'Adventure',
        'description': 'A nature lover\'s paradise with rainforests, volcanoes, wildlife, and thrilling adventure activities.',
        'attractions': 'Arenal Volcano, Monteverde Cloud Forest, Manuel Antonio, Zip-lining, Tortuguero Canals',
        'estimated_cost': 95000,
        'best_time': 'December to April',
        'latitude': 9.7489,
        'longitude': -83.7534,
        'image_url': 'https://images.unsplash.com/photo-1518259102261-b40117eabbc9?w=800'
    },
    {
        'name': 'Egypt',
        'type': 'Cultural',
        'description': 'Home to the ancient pyramids, pharaohs, and one of the world\'s oldest civilizations with rich historical heritage.',
        'attractions': 'Pyramids of Giza, Luxor Temple, Valley of the Kings, Sphinx, Nile Cruise',
        'estimated_cost': 75000,
        'best_time': 'October to April',
        'latitude': 26.8206,
        'longitude': 30.8025,
        'image_url': 'https://images.unsplash.com/photo-1539650116574-8efeb43e2750?w=800'
    },
    # Local Karnataka Destinations
    {
        'name': 'Muddenhalli',
        'type': 'Cultural',
        'description': 'A peaceful village in Chikkaballapur district, known for its serene environment and proximity to tourist spots like Nandi Hills.',
        'attractions': 'Nandi Hills, Muddenhalli Village, Bhoga Nandeeshwara Temple, Tipu Sultan Fort',
        'estimated_cost': 5000,
        'best_time': 'October to March',
        'latitude': 13.1048,
        'longitude': 77.7454,
        'image_url': 'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800'
    },
    {
        'name': 'Chikkaballapur',
        'type': 'Hill',
        'description': 'A historical town in Karnataka known for its rich heritage, temples, and scenic hill stations nearby.',
        'attractions': 'Nandi Hills, Chikkaballapur Fort, Bhoga Nandeeshwara Temple, Skandagiri',
        'estimated_cost': 8000,
        'best_time': 'October to March',
        'latitude': 13.4356,
        'longitude': 77.7217,
        'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800'
    },
    {
        'name': 'Nandi Hills',
        'type': 'Hill',
        'description': 'A beautiful hill station near Bangalore, perfect for weekend getaways with pleasant weather and stunning views.',
        'attractions': 'Tipu Sultan\'s Drop, Anand Art Gallery, Nandi Temple, Bhoga Nandeeshwara Temple',
        'estimated_cost': 6000,
        'best_time': 'September to May',
        'latitude': 13.3700,
        'longitude': 77.6833,
        'image_url': 'https://images.unsplash.com/photo-1508193638397-1c4234db14d9?w=800'
    },
    {
        'name': 'Bangalore',
        'type': 'City',
        'description': 'The Silicon Valley of India - a vibrant city with beautiful parks, historical monuments, and excellent food.',
        'attractions': 'Bangalore Palace, Cubbon Park, Lal Bagh, MG Road, Bannerghatta National Park',
        'estimated_cost': 15000,
        'best_time': 'October to February',
        'latitude': 12.9716,
        'longitude': 77.5946,
        'image_url': 'https://images.unsplash.com/photo-1596496050827-8299e0220de1?w=800'
    },
    {
        'name': 'Mysore',
        'type': 'Cultural',
        'description': 'The cultural capital of Karnataka with magnificent palaces, rich heritage, and vibrant markets.',
        'attractions': 'Mysore Palace, Chamundeshwari Temple, Brindavan Gardens, St. Philomena\'s Church',
        'estimated_cost': 12000,
        'best_time': 'October to March',
        'latitude': 12.2958,
        'longitude': 76.6394,
        'image_url': 'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800'
    },
    {
        'name': 'Coorg',
        'type': 'Hill',
        'description': 'The Scotland of India - a beautiful hill station with lush coffee plantations and stunning waterfalls.',
        'attractions': 'Abbey Falls, Raja\'s Seat, Dubare Elephant Camp, Namdroling Monastery',
        'estimated_cost': 18000,
        'best_time': 'October to March',
        'latitude': 12.3375,
        'longitude': 75.8069,
        'image_url': 'https://images.unsplash.com/photo-1508193638397-1c4234db14d9?w=800'
    },
    {
        'name': 'Mangalore',
        'type': 'Beach',
        'description': 'A coastal city in Karnataka with beautiful beaches, ancient temples, and delicious cuisine.',
        'attractions': 'Panambur Beach, Kadri Manjunath Temple, St. Aloysius Chapel, Sultan Battery',
        'estimated_cost': 15000,
        'best_time': 'October to March',
        'latitude': 12.9141,
        'longitude': 74.8560,
        'image_url': 'https://images.unsplash.com/photo-1518546979797-8494b522d09b?w=800'
    },
    {
        'name': 'Hampi',
        'type': 'Cultural',
        'description': 'A UNESCO World Heritage Site with ancient ruins, boulder-strewn landscapes, and rich historical significance.',
        'attractions': 'Virupaksha Temple, Hampi Bazaar, Vittala Temple, Lotus Mahal, Elephant Stables',
        'estimated_cost': 10000,
        'best_time': 'October to March',
        'latitude': 15.3350,
        'longitude': 76.4600,
        'image_url': 'https://images.unsplash.com/photo-1565008576549-57569a49371d?w=800'
    }
]

# ML-based AI Recommendation Engine using K-Nearest Neighbors
class MLRecommendationEngine:
    """Machine Learning based recommendation engine using KNN"""
    
    def __init__(self):
        self.destinations = DESTINATIONS
        self.type_encoder = LabelEncoder()
        self.budget_encoder = LabelEncoder()
        self.travel_type_encoder = LabelEncoder()
        self.season_encoder = LabelEncoder()
        self.scaler = MinMaxScaler()
        self.model = NearestNeighbors(n_neighbors=5, metric='cosine')
        self._train_model()
    
    def _encode_type(self, dest_type):
        """Encode destination type"""
        types = ['Beach', 'Hill', 'City', 'Adventure', 'Cultural']
        if dest_type not in types:
            return 2  # Default to City
        return types.index(dest_type)
    
    def _encode_budget(self, cost):
        """Encode budget level based on cost"""
        if cost < 40000:
            return 0  # Low
        elif cost < 100000:
            return 1  # Medium
        else:
            return 2  # High
    
    def _encode_season(self, season):
        """Encode seasonal preference"""
        seasons = ['Summer', 'Monsoon', 'Autumn', 'Winter']
        if season not in seasons:
            return 1  # Default to Monsoon
        return seasons.index(season)
    
    def _encode_travel_type(self, travel_type):
        """Encode travel type"""
        types = ['Solo', 'Family', 'Friends']
        if travel_type not in types:
            return 0  # Default to Solo
        return types.index(travel_type)
    
    def _create_feature_vector(self, destination):
        """Create feature vector for a destination"""
        return [
            self._encode_type(destination['type']),
            self._encode_budget(destination['estimated_cost']),
            destination['estimated_cost'] / 200000,  # Normalized cost
            destination['latitude'] / 90,  # Normalized latitude
            destination['longitude'] / 180  # Normalized longitude
        ]
    
    def _train_model(self):
        """Train the KNN model on destination data"""
        features = []
        for dest in self.destinations:
            features.append(self._create_feature_vector(dest))
        
        self.features_array = np.array(features)
        self.scaled_features = self.scaler.fit_transform(self.features_array)
        self.model.fit(self.scaled_features)
    
    def get_recommendations(self, preferences):
        """Get ML-based recommendations"""
        # Create user preference vector
        user_type = self._encode_type(preferences['destination_type'])
        user_budget = {'Low': 0, 'Medium': 1, 'High': 2}.get(preferences['budget'], 1)
        user_travel_type = self._encode_travel_type(preferences['travel_type'])
        user_season = self._encode_season(preferences['season'])
        
        # Calculate budget in rupees for matching
        budget_map = {'Low': 30000, 'Medium': 60000, 'High': 150000}
        user_budget_cost = budget_map.get(preferences['budget'], 60000)
        
        # Create user feature vector
        user_vector = np.array([
            user_type,
            user_budget,
            user_budget_cost / 200000,
            0.15,  # Default to central India coordinates
            0.45
        ]).reshape(1, -1)
        
        scaled_user = self.scaler.transform(user_vector)
        
        # Find nearest neighbors
        distances, indices = self.model.kneighbors(scaled_user)
        
        # Get recommended destinations with scores
        recommendations = []
        for i, idx in enumerate(indices[0]):
            dest = self.destinations[idx].copy()
            # Calculate match score based on multiple factors
            type_match = 100 if dest['type'].lower() == preferences['destination_type'].lower() else 30
            budget_match = 100 if self._encode_budget(dest['estimated_cost']) <= user_budget else 40
            
            # Travel type bonus
            travel_bonus = 0
            if preferences['travel_type'] == 'Solo' and dest['type'] in ['Adventure', 'Cultural']:
                travel_bonus = 15
            elif preferences['travel_type'] == 'Family' and dest['type'] in ['Beach', 'City']:
                travel_bonus = 15
            elif preferences['travel_type'] == 'Friends' and dest['type'] in ['Adventure', 'Beach', 'City']:
                travel_bonus = 15
            
            # ML model confidence based on distance
            ml_confidence = max(0, (1 - distances[0][i]) * 100)
            
            # Final score
            final_score = int((type_match * 0.4 + budget_match * 0.3 + travel_bonus * 0.15 + ml_confidence * 0.15))
            dest['score'] = min(99, final_score)
            recommendations.append(dest)
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]

# Initialize ML recommendation engine
ml_engine = MLRecommendationEngine()

# AI Recommendation Engine (Legacy - for reference)
def get_recommendations(preferences):
    """AI-powered recommendation engine based on user preferences"""
    return ml_engine.get_recommendations(preferences)

# AI Itinerary Generator
def generate_itinerary(destination, days, travel_type):
    """Generate a day-wise travel plan using AI logic"""
    itinerary = []
    
    # Sample activities based on destination type
    activity_pool = {
        'Beach': [
            'Morning beach walk and sunrise viewing',
            'Water sports activities (snorkeling, diving, jet skiing)',
            'Beachside lunch with local cuisine',
            'Afternoon relaxation and swimming',
            'Sunset cruise or dolphin watching',
            'Beach party or bonfire evening'
        ],
        'Hill': [
            'Early morning mountain hike',
            'Visit to local viewpoints and scenic spots',
            'Traditional mountain lunch',
            'Explore nearby villages and tea gardens',
            'Photography session at sunset point',
            'Bonfire with local music'
        ],
        'City': [
            'City tour and landmark visits',
            'Museum or art gallery exploration',
            'Local street food tour',
            'Shopping at local markets',
            'Evening entertainment and nightlife',
            'Cultural show or performance'
        ],
        'Adventure': [
            'Early morning adventure activity',
            'Trekking or exploration of trails',
            'Lunch at a scenic spot',
            'River rafting or climbing',
            'Visit to natural wonders',
            'Evening meditation or yoga'
        ],
        'Cultural': [
            'Temple or heritage site visit',
            'Local cultural museum tour',
            'Traditional cooking class',
            'Visit to artisan workshops',
            'Evening cultural performance',
            'Reflection and photography'
        ]
    }
    
    activities = activity_pool.get(destination.get('type', 'City'), activity_pool['City'])
    
    # Generate day-wise plan
    for day in range(1, days + 1):
        daily_activities = []
        
        if day == 1:
            daily_activities = [
                'Arrival and hotel check-in',
                'Orientation walk around the area',
                'Welcome dinner at local restaurant',
                'Rest and prepare for the trip'
            ]
        elif day == days:
            daily_activities = [
                'Final sightseeing and shopping',
                'Packing and checkout',
                'Last minute exploration',
                'Departure'
            ]
        else:
            # Select random activities for the day
            selected = random.sample(activities, min(4, len(activities)))
            daily_activities = selected + [
                'Breakfast at hotel',
                'Dinner at local restaurant'
            ]
        
        itinerary.append({
            'day': day,
            'activities': daily_activities
        })
    
    return itinerary

# Travel Chatbot - AI Assistant (Enhanced with relaxed, friendly responses like ChatGPT/Gemini)
def get_chatbot_response(user_message):
    """AI-powered travel assistant chatbot with relaxed, friendly responses"""
    message = user_message.lower()
    
    responses = {
        'best_places': [
            "Hey there! Looking for some cool places to explore? Here are my faves:\n\nBeach vibes: Maldives, Goa, Bali are super relaxing!\n\nHill stations: Manali, Ladakh, Coorg - perfect for nature lovers\n\nCultural spots: Kyoto, Rome, Hampi - each has such amazing history\n\nAdventure: Rishikesh, Swiss Alps - get that adrenaline pumping!\n\nAlso, check out local Karnataka gems like Nandi Hills, Muddenhalli, and Mysore - they're absolutely worth visiting!",
            "Ooh, I love this question! Here's my top picks:\n\nFor beaches: Go for Maldives or Goa - crystal clear waters!\n\nHills: Coorg and Nandi Hills are amazing weekend getaways\n\nAdventure: Rishikesh is lit with all the activities!\n\nCultural: Hampi and Mysore have the richest heritage\n\nWhat kind of vibe are you going for?"
        ],
        'budget': [
            "So you want to travel smart, huh? Here are some cool tips:\n\nTravel in off-season - prices drop so much!\n\nBook flights mid-week for cheaper rates\n\nStay in local guesthouses instead of fancy hotels\n\nEat at local food stalls - way tastier and cheaper!\n\nUse public transport or rent a bike\n\nFor Karnataka trips, you can explore Muddenhalli or Chikkaballapur on a shoestring budget - super affordable and beautiful!",
            "Money matters! Here's my budget travel hacks:\n\nTry Nandi Hills or local Karnataka spots - super affordable\n\nUse KSRTC buses - they're cheap and connect everywhere\n\nBook stays via local websites instead of big platforms\n\nCarry a water bottle and snacks\n\nTravel in groups to split costs\n\nYou can easily do a weekend trip under 5000 in Karnataka!"
        ],
        'tips': [
            "Here's some chill travel advice:\n\nKeep digital copies of all docs on Google Drive\n\nLearn a few local words - people appreciate it!\n\nAlways carry a first-aid kit\n\nPack light - you'll thank yourself later\n\nDon't over-plan - leave room for adventures!\n\nFor local Karnataka travel, download KSRTC app for bus timings\n\nTravel is about the journey, not just the destination!",
            "Let me share some golden tips!\n\nAlways have travel insurance\n\nKeep some cash handy - not everywhere accepts cards\n\nWear comfortable shoes - you'll walk a lot!\n\nTry local food - it's part of the experience\n\nBe respectful of local customs\n\nFor Karnataka, check KSRTC bus timings before heading out\n\nSafe travels!"
        ],
        'best_time': [
            "Great question! Here's the lowdown:\n\nBeach places: Oct-March is prime time\n\nHill stations: Mar-June or Oct-Nov\n\nCultural sites: Oct-March\n\nAvoid monsoons for most places\n\nFor Karnataka specifically:\n\nNandi Hills: Best Sept-May\n\nCoorg: Oct-March\n\nHampi: Oct-Feb\n\nMysore: Oct-March\n\nAlways check weather before you go!",
            "Timing is everything! My advice:\n\nWinter (Oct-Feb) is great for most places\n\nSummer can be brutal in plains - avoid!\n\nMonsoon (June-Sept) is hit or miss\n\nFor local Karnataka trips:\n\nNandi Hills: Pleasant weather Sept-May\n\nCoorg: Post-monsoon is beautiful\n\nHampi: Winter is perfect\n\nWould you like me to check current weather for a place?"
        ],
        'packing': [
            "Pack smart, travel light! Essentials:\n\nComfortable clothes as per weather\n\nPower bank - so important!\n\nBasic medicines\n\nReusable water bottle\n\nGood camera (or phone!)\n\nSunscreen and sunglasses\n\nSmall backpack for day trips\n\nFor local Karnataka trips:\n\nLight cotton clothes\n\nWalking shoes\n\nUmbrella/raincoat during monsoon\n\nWhat destination are you planning for?",
            "Here's my packing list!\n\nClothes (weather appropriate)\n\nToiletries kit\n\nPower bank + charger\n\nBasic meds\n\nWater bottle\n\nCamera\n\nSmall daypack\n\nFor Karnataka getaways:\n\nCotton clothes work best\n\nComfortable sandals/shoes\n\nRaincoat during monsoon\n\nNeed help with anything specific?"
        ],
        'hotels': [
            "Looking for a place to crash? Here's the tea:\n\nFor booking:\n\nUse Booking.com, Airbnb, or MMT\n\nCheck reviews carefully\n\nLocation matters - near attractions = less travel time\n\nLocal Karnataka options:\n\nMuddenhalli: Local homestays available\n\nNandi Hills: Few resorts, book early!\n\nCoorg: Lots of coffee estate stays\n\nBangalore: All budget options available\n\nWhat's your budget? I can suggest better!",
            "Finding the perfect stay!\n\nPro tips:\n\nCheck distance to main attractions\n\nRead recent reviews\n\nCompare prices on multiple sites\n\nLook for free cancellation options\n\nBudget options:\n\nOYO for budget stays\n\nAirbnb for unique experiences\n\nHomestays for local experience\n\nFor your area, I'd recommend checking near Nandi Hills or local Chikkaballapur stays!"
        ],
        'transport': [
            "Getting around made easy!\n\nKarnataka transport:\n\nKSRTC buses - super cheap, connects everywhere\n\nPrivate buses for comfort\n\nTrains - book via IRCTC\n\nMetro in Bangalore\n\nRent bikes/cars for flexibility\n\nFor local trips:\n\nAuto rickshaws in cities\n\nKSRTC app for bus booking\n\nOla/Uber in major cities\n\nWant to know transport options for a specific place?"
        ],
        'weather': [
            "Want to know about weather?\n\nFor accurate weather info, you can:\n\nCheck Google Weather\n\nUse Weather.com\n\nDownload Weather apps\n\nGenerally:\n\nWinter (Nov-Feb): Pleasant\n\nSummer (Mar-May): Hot\n\nMonsoon (June-Sept): Rainy\n\nWould you like me to help you check weather for a specific destination? Just ask!",
            "Weather check!\n\nFor your trip planning, here's the seasonal breakdown:\n\nMost places are best during winter\n\nAvoid summers if you can\n\nMonsoons can be tricky but beautiful\n\nFor Karnataka:\n\nNandi Hills is pleasant most of the year\n\nCoorg looks amazing post-monsoon\n\nLet me know which place you're planning to visit!"
        ],
        'nearby': [
            "Finding stuff nearby!\n\nFor nearby attractions/food:\n\nUse Google Maps\n\nCheck TripAdvisor\n\nAsk locals - they know best!\n\nFor hotels near you:\n\nSearch on Booking.com or MMT\n\nFor restaurants:\n\nZomato/Swiggy for delivery\n\nGoogle Maps for dine-out options\n\nTell me your location and I can help better!",
            "Looking for nearby options?\n\nQuick tips:\n\nGoogle Maps is your best friend\n\nFor hotels: Check Booking.com, MMT\n\nFor food: Zomato, Swiggy\n\nFor attractions: TripAdvisor\n\nFor local Karnataka: Ask locals for hidden gems!\n\nWhat's your current location?"
        ],
        'translate': [
            "Need help with translations?\n\nKannada basics:\n\nNamaste - Hello\n\nShubhodaya - Good morning\n\nDhanyavaadagalu - Thank you\n\nHogu - Go\n\nIdli - Idli\n\nDose - Dosa\n\nFor more help, use Google Translate app!",
            "Learning local languages is fun!\n\nSome useful Kannada phrases:\n\nHello - Namaste\n\nThank you - Dhanyavaadagalu\n\nGood morning - Shubhodaya\n\nHow much? - Eshtu?\n\nWater - Neeru\n\nFood - Oota\n\nGood - Chennagide\n\nUse Google Translate for more!"
        ],
        'default': [
            "Hey! I'm your travel buddy! Ask me about:\n\nBest places to visit\n\nBudget travel tips\n\nWhat to pack\n\nBest time to travel\n\nHotels and stays\n\nTransport options\n\nWeather info\n\nNearby attractions\n\nLocal language tips\n\nI also know about local Karnataka spots like Muddenhalli, Nandi Hills, Coorg, and more! Where do you want to go?",
            "Yo! Let's plan your next adventure!\n\nI'm here to help with:\n\nDestination suggestions\n\nBudget planning\n\nTravel tips\n\nTransport info\n\nHotel bookings\n\nLocal experiences\n\nJust tell me what you need! And hey, I can also help with basic translations for your trips!"
        ]
    }
    
    if 'place' in message or 'destination' in message or 'visit' in message or 'go' in message:
        return random.choice(responses['best_places'])
    elif 'budget' in message or 'cheap' in message or 'cost' in message or 'money' in message:
        return random.choice(responses['budget'])
    elif 'tip' in message or 'advice' in message:
        return random.choice(responses['tips'])
    elif 'time' in message or 'season' in message or 'weather' in message or 'temperature' in message:
        return random.choice(responses['best_time'])
    elif 'pack' in message or 'carry' in message:
        return random.choice(responses['packing'])
    elif 'hotel' in message or 'stay' in message or 'room' in message or 'resort' in message:
        return random.choice(responses['hotels'])
    elif 'bus' in message or 'train' in message or 'transport' in message or 'reach' in message:
        return random.choice(responses['transport'])
    elif 'weather' in message or 'rain' in message or 'hot' in message or 'cold' in message:
        return random.choice(responses['weather'])
    elif 'near' in message or 'nearby' in message or 'around' in message or 'food' in message or 'restaurant' in message:
        return random.choice(responses['nearby'])
    elif 'translate' in message or 'language' in message or 'kannada' in message or 'local language' in message:
        return random.choice(responses['translate'])
    else:
        return random.choice(responses['default'])

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('travel_planner.db')
        c = conn.cursor()
        
        # Check if email already exists
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        if c.fetchone():
            flash('Email already registered!', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        # Check if username already exists
        c.execute('SELECT id FROM users WHERE username = ?', (username,))
        if c.fetchone():
            flash('Username already taken!', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        # Insert new user
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                  (username, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('travel_planner.db')
        c = conn.cursor()
        c.execute('SELECT id, username, email, password FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            user_obj = User(user[0], user[1], user[2])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('travel_planner.db')
    c = conn.cursor()
    
    # Get preferences
    c.execute('SELECT * FROM user_preferences WHERE user_id = ?', (current_user.id,))
    pref_row = c.fetchone()
    preferences = None
    if pref_row:
        preferences = {
            'id': pref_row[0],
            'user_id': pref_row[1],
            'destination_type': pref_row[2],
            'budget': pref_row[3],
            'travel_days': pref_row[4],
            'travel_type': pref_row[5],
            'season': pref_row[6]
        }
    
    # Get itineraries
    c.execute('SELECT * FROM itineraries WHERE user_id = ? ORDER BY created_at DESC', (current_user.id,))
    itinerary_rows = c.fetchall()
    itineraries = []
    for row in itinerary_rows:
        itineraries.append({
            'id': row[0],
            'user_id': row[1],
            'destination': row[2],
            'days': row[3],
            'itinerary_data': row[4],
            'created_at': row[5]
        })
    
    conn.close()
    return render_template('dashboard.html', preferences=preferences, itineraries=itineraries)

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences_page():
    if request.method == 'POST':
        destination_type = request.form.get('destination_type')
        budget = request.form.get('budget')
        travel_days = int(request.form.get('travel_days'))
        travel_type = request.form.get('travel_type')
        season = request.form.get('season')
        
        conn = sqlite3.connect('travel_planner.db')
        c = conn.cursor()
        
        # Check if preferences exist
        c.execute('SELECT id FROM user_preferences WHERE user_id = ?', (current_user.id,))
        existing = c.fetchone()
        
        if existing:
            c.execute('''UPDATE user_preferences SET 
                destination_type = ?, budget = ?, travel_days = ?, travel_type = ?, season = ?
                WHERE user_id = ?''',
                (destination_type, budget, travel_days, travel_type, season, current_user.id))
        else:
            c.execute('''INSERT INTO user_preferences 
                (user_id, destination_type, budget, travel_days, travel_type, season) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (current_user.id, destination_type, budget, travel_days, travel_type, season))
        
        conn.commit()
        conn.close()
        
        flash('Preferences saved!', 'success')
        return redirect(url_for('recommendations'))
    
    return render_template('preferences.html')

@app.route('/recommendations')
@login_required
def recommendations():
    conn = sqlite3.connect('travel_planner.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user_preferences WHERE user_id = ?', (current_user.id,))
    pref_row = c.fetchone()
    conn.close()
    
    if not pref_row:
        flash('Please set your travel preferences first!', 'warning')
        return redirect(url_for('preferences_page'))
    
    preferences = {
        'destination_type': pref_row[2],
        'budget': pref_row[3],
        'travel_days': pref_row[4],
        'travel_type': pref_row[5],
        'season': pref_row[6]
    }
    
    recommended_destinations = get_recommendations(preferences)
    return render_template('recommendations.html', destinations=recommended_destinations, preferences=preferences)

@app.route('/destination/<destination_name>')
@login_required
def destination_detail(destination_name):
    dest = next((d for d in DESTINATIONS if d['name'] == destination_name), None)
    return render_template('destination.html', destination=dest)

@app.route('/generate_itinerary', methods=['POST'])
@login_required
def generate_itinerary_route():
    data = request.get_json()
    destination_name = data.get('destination')
    days = int(data.get('days', 3))
    travel_type = data.get('travel_type', 'Solo')
    
    dest = next((d for d in DESTINATIONS if d['name'] == destination_name), None)
    if not dest:
        return jsonify({'error': 'Destination not found'}), 404
    
    itinerary = generate_itinerary(dest, days, travel_type)
    
    # Save itinerary to database
    conn = sqlite3.connect('travel_planner.db')
    c = conn.cursor()
    c.execute('''INSERT INTO itineraries (user_id, destination, days, itinerary_data) 
                 VALUES (?, ?, ?, ?)''',
              (current_user.id, destination_name, days, str(itinerary)))
    conn.commit()
    conn.close()
    
    return jsonify({
        'destination': destination_name,
        'days': days,
        'itinerary': itinerary
    })

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    user_message = request.get_json().get('message', '')
    response = get_chatbot_response(user_message)
    return jsonify({'response': response})

@app.route('/gallery')
@login_required
def gallery():
    destinations = DESTINATIONS
    return render_template('gallery.html', destinations=destinations)

@app.route('/map')
@login_required
def travel_map():
    destinations = DESTINATIONS
    return render_template('map.html', destinations=destinations)

# Weather information route
@app.route('/weather/<destination_name>')
@login_required
def get_weather(destination_name):
    """Get weather information for a destination"""
    dest = next((d for d in DESTINATIONS if d['name'].lower() == destination_name.lower()), None)
    
    if not dest:
        return jsonify({'error': 'Destination not found'}), 404
    
    # Simulated weather data based on best time to visit
    weather_info = {
        'destination': dest['name'],
        'latitude': dest['latitude'],
        'longitude': dest['longitude'],
        'best_time': dest['best_time'],
        'current_weather': 'Check Google Weather for real-time updates',
        'temperature': 'Varies by season',
        'tips': f"The best time to visit {dest['name']} is {dest['best_time']}"
    }
    
    return jsonify(weather_info)

# Translate route
@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    """Simple translation helper"""
    data = request.get_json()
    text = data.get('text', '').lower()
    target_lang = data.get('language', 'en')
    
    # Simple Kannada translations
    translations = {
        'hello': 'Namaste (ನಮಸ್ತೆ)',
        'thank you': 'Dhanyavaadagalu (ಧನ್ಯವಾದಗಳು)',
        'good morning': 'Shubhodaya (ಶುಭೋದಯ)',
        'good night': 'Shubha ratri (ಶುಭ ರಾತ್ರಿ)',
        'how much': 'Eshtu (ಎಷ್ಟು)',
        'water': 'Neeru (ನೀರು)',
        'food': 'Oota (ಊಟ)',
        'help': 'Sahaya (ಸಹಾಯ)',
        'yes': 'Haan (ಹೌದು)',
        'no': 'Illa (ಇಲ್ಲ)',
        'good': 'Chennagide (ಚೆನ್ನಗಿದೆ)',
        'beautiful': 'Sundara (ಸುಂದರ)',
        'idli': 'Idli (ಇಡ್ಲಿ)',
        'dosa': 'Dose (ದೋಸೆ)',
        'rice': 'Akki (ಅಕ್ಕಿ)',
        'curry': 'Saaru (ಸಾರು)'
    }
    
    result = translations.get(text, 'Translation not available. Use Google Translate for more phrases.')
    
    return jsonify({'translation': result, 'original': text, 'language': 'Kannada'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

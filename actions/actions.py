# =============================================================================
# Eco-Travel Advisor - Custom Actions
# =============================================================================
# All custom Rasa actions for hotel recommendations, transport, carbon
# calculation, activities, human handover, and trip summary.
# =============================================================================

from typing import Any, Text, Dict, List, Optional
import logging
import math

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, Restarted, ConversationPaused
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)

# =============================================================================
# MOCK DATA: Eco-Friendly Hotels Database
# =============================================================================
ECO_HOTELS_DB = {
    "costa rica": [
        {
            "name": "Lapa Rios Eco Lodge",
            "rating": 5,
            "price_per_night": 350,
            "eco_score": 98,
            "certifications": ["Rainforest Alliance", "CST Gold"],
            "features": ["Solar powered", "Rainforest conservation", "Local staff", "Organic farm"],
            "description": "Award-winning eco-lodge in the Osa Peninsula rainforest."
        },
        {
            "name": "Finca Rosa Blanca Coffee Plantation",
            "rating": 4,
            "price_per_night": 220,
            "eco_score": 92,
            "certifications": ["CST Gold", "Green Globe"],
            "features": ["Organic coffee farm", "Renewable energy", "Water recycling"],
            "description": "Boutique hotel on a working organic coffee plantation."
        },
        {
            "name": "Arenas del Mar Beach Resort",
            "rating": 4,
            "price_per_night": 180,
            "eco_score": 85,
            "certifications": ["Blue Flag", "CST Silver"],
            "features": ["Beach conservation", "Local cuisine", "Wildlife monitoring"],
            "description": "Eco-resort dedicated to marine and wildlife conservation."
        }
    ],
    "iceland": [
        {
            "name": "Ion Adventure Hotel",
            "rating": 5,
            "price_per_night": 400,
            "eco_score": 96,
            "certifications": ["Nordic Swan", "Green Globe"],
            "features": ["Geothermal heating", "Northern lights view", "Electric vehicles"],
            "description": "Iceland's most sustainable luxury hotel near Thingvellir."
        },
        {
            "name": "Deplar Farm",
            "rating": 5,
            "price_per_night": 900,
            "eco_score": 94,
            "certifications": ["Vakinn Eco-Label"],
            "features": ["100% renewable energy", "Organic farming", "Community employment"],
            "description": "Remote eco-retreat on a former sheep farm in the fjords."
        },
        {
            "name": "Frost Hostel Reykjavik",
            "rating": 3,
            "price_per_night": 65,
            "eco_score": 80,
            "certifications": ["Green Key"],
            "features": ["Energy efficient", "Local products", "Bike rentals"],
            "description": "Budget-friendly eco-certified hostel in downtown Reykjavik."
        }
    ],
    "bali": [
        {
            "name": "Bambu Indah",
            "rating": 5,
            "price_per_night": 280,
            "eco_score": 99,
            "certifications": ["Green Globe", "PATA Gold"],
            "features": ["Bamboo architecture", "Organic garden", "Natural pool", "Zero waste"],
            "description": "Iconic eco-resort built with traditional Javanese antique homes."
        },
        {
            "name": "Shankara Healing Village",
            "rating": 4,
            "price_per_night": 150,
            "eco_score": 88,
            "certifications": ["Green Globe"],
            "features": ["Ayurvedic spa", "Permaculture garden", "Rainwater harvesting"],
            "description": "Holistic eco-retreat focused on wellness and sustainability."
        }
    ],
    "default": [
        {
            "name": "Generic Eco Hotel Premier",
            "rating": 4,
            "price_per_night": 200,
            "eco_score": 85,
            "certifications": ["Green Key", "ISO 14001"],
            "features": ["Solar panels", "Water conservation", "Local sourcing", "EV charging"],
            "description": "Certified eco-friendly hotel with comprehensive sustainability programs."
        },
        {
            "name": "Sustainable Stays Boutique",
            "rating": 3,
            "price_per_night": 120,
            "eco_score": 78,
            "certifications": ["Green Globe"],
            "features": ["Energy efficient", "Recycling program", "Organic breakfast"],
            "description": "Comfortable boutique hotel with solid eco credentials."
        },
        {
            "name": "EcoNest Community Lodge",
            "rating": 4,
            "price_per_night": 95,
            "eco_score": 90,
            "certifications": ["Fair Trade Tourism", "Green Key"],
            "features": ["Community owned", "Renewable energy", "Zero plastic policy"],
            "description": "Community-run lodge with strong social and environmental impact."
        }
    ]
}

# =============================================================================
# MOCK DATA: Transport Options + Emissions
# =============================================================================
TRANSPORT_DATA = {
    "flight": {
        "co2_per_km_per_person": 0.255,   # kg CO2 per km per person (economy)
        "description": "Air travel (economy class)",
        "eco_rating": "Low",
        "cost_per_km": 0.12,
        "advantages": ["Fastest option", "Long-distance capable"],
        "disadvantages": ["Highest CO2 emitter", "Airport overhead", "Noise pollution"],
        "tips": "Choose direct flights, pack light, offset with certified programs"
    },
    "train": {
        "co2_per_km_per_person": 0.041,
        "description": "Electric/diesel rail travel",
        "eco_rating": "High",
        "cost_per_km": 0.08,
        "advantages": ["Low emissions", "City-centre to city-centre", "Scenic routes", "Comfortable"],
        "disadvantages": ["Slower than flying", "Limited long-distance routes"],
        "tips": "Book in advance for best prices, use night trains to save accommodation"
    },
    "bus": {
        "co2_per_km_per_person": 0.089,
        "description": "Coach/intercity bus travel",
        "eco_rating": "Medium-High",
        "cost_per_km": 0.04,
        "advantages": ["Very affordable", "Low emissions", "Wide coverage"],
        "disadvantages": ["Slowest option", "Less comfortable for long trips"],
        "tips": "Modern coaches can be surprisingly comfortable and eco-friendly"
    },
    "electric vehicle": {
        "co2_per_km_per_person": 0.053,
        "description": "Electric vehicle rental",
        "eco_rating": "High",
        "cost_per_km": 0.06,
        "advantages": ["Zero tailpipe emissions", "Flexible itinerary", "Quiet", "Cheap to run"],
        "disadvantages": ["Range anxiety", "Charging infrastructure varies"],
        "tips": "Use renewable energy charging points, plan routes around charging stations"
    },
    "ferry": {
        "co2_per_km_per_person": 0.113,
        "description": "Ferry/boat travel",
        "eco_rating": "Medium",
        "cost_per_km": 0.07,
        "advantages": ["Great experience", "No traffic", "Unique perspective"],
        "disadvantages": ["Slower", "Weather dependent", "Limited routes"],
        "tips": "Modern ferries are significantly cleaner than older vessels"
    },
    "cycling": {
        "co2_per_km_per_person": 0.0,
        "description": "Cycling / e-bike",
        "eco_rating": "Perfect",
        "cost_per_km": 0.01,
        "advantages": ["Zero emissions", "Healthy", "Free local exploration", "Authentic experience"],
        "disadvantages": ["Distance limited", "Weather dependent", "Physical effort"],
        "tips": "Many destinations have excellent bike rental networks"
    }
}

# =============================================================================
# MOCK DATA: Activities Database
# =============================================================================
ACTIVITIES_DB = {
    "costa rica": [
        {"name": "Rainforest Canopy Tour", "type": "eco-adventure", "carbon_impact": "zero", "price": 85, "supports_local": True},
        {"name": "Sea Turtle Nesting Night Walk", "type": "wildlife", "carbon_impact": "zero", "price": 50, "supports_local": True},
        {"name": "Indigenous Community Visit", "type": "cultural", "carbon_impact": "zero", "price": 40, "supports_local": True},
        {"name": "Organic Coffee Farm Tour", "type": "cultural", "carbon_impact": "zero", "price": 30, "supports_local": True},
        {"name": "Mangrove Kayaking", "type": "eco-adventure", "carbon_impact": "zero", "price": 65, "supports_local": True},
    ],
    "iceland": [
        {"name": "Northern Lights Photography Tour", "type": "natural wonder", "carbon_impact": "minimal", "price": 120, "supports_local": True},
        {"name": "Geothermal Cooking Class", "type": "cultural", "carbon_impact": "zero", "price": 90, "supports_local": True},
        {"name": "Glacier Hiking with Local Guide", "type": "eco-adventure", "carbon_impact": "minimal", "price": 110, "supports_local": True},
        {"name": "Icelandic Horse Riding", "type": "eco-adventure", "carbon_impact": "zero", "price": 80, "supports_local": True},
        {"name": "Whale Watching (Sustainable Operator)", "type": "wildlife", "carbon_impact": "low", "price": 95, "supports_local": True},
    ],
    "bali": [
        {"name": "Subak Rice Field Walk", "type": "cultural", "carbon_impact": "zero", "price": 25, "supports_local": True},
        {"name": "Temple Ceremony Participation", "type": "cultural", "carbon_impact": "zero", "price": 20, "supports_local": True},
        {"name": "Cooking Class with Local Family", "type": "cultural", "carbon_impact": "zero", "price": 45, "supports_local": True},
        {"name": "Sacred Monkey Forest Visit", "type": "wildlife", "carbon_impact": "zero", "price": 5, "supports_local": True},
        {"name": "Traditional Batik Making Workshop", "type": "cultural", "carbon_impact": "zero", "price": 35, "supports_local": True},
    ],
    "default": [
        {"name": "Local Guided Walking Tour", "type": "cultural", "carbon_impact": "zero", "price": 30, "supports_local": True},
        {"name": "Community Market Visit", "type": "cultural", "carbon_impact": "zero", "price": 0, "supports_local": True},
        {"name": "Organic Farm Visit & Meal", "type": "cultural", "carbon_impact": "zero", "price": 55, "supports_local": True},
        {"name": "Local Craft Workshop", "type": "cultural", "carbon_impact": "zero", "price": 40, "supports_local": True},
        {"name": "Nature Reserve Guided Hike", "type": "eco-adventure", "carbon_impact": "zero", "price": 25, "supports_local": True},
        {"name": "Sunset Cycling Tour", "type": "eco-adventure", "carbon_impact": "zero", "price": 35, "supports_local": True},
    ]
}

# =============================================================================
# MOCK DATA: Carbon Offset Programs
# =============================================================================
CARBON_OFFSET_PROGRAMS = [
    {
        "name": "Gold Standard Reforestation",
        "price_per_tonne": 15,
        "description": "Plant trees in deforested areas with verified carbon sequestration.",
        "certification": "Gold Standard",
        "url": "goldstandard.org"
    },
    {
        "name": "Verified Carbon Standard (Verra)",
        "price_per_tonne": 12,
        "description": "Industrial renewable energy projects reducing grid emissions.",
        "certification": "VCS",
        "url": "verra.org"
    },
    {
        "name": "Cool Effect Community Projects",
        "price_per_tonne": 10,
        "description": "Community-based clean cookstove and biogas projects.",
        "certification": "CDM",
        "url": "cooleffect.org"
    },
    {
        "name": "Atmosfair Flight Offset",
        "price_per_tonne": 23,
        "description": "High-quality offsets specifically designed for aviation emissions.",
        "certification": "CDM/Gold Standard",
        "url": "atmosfair.de"
    }
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_budget(budget_str: Optional[str]) -> float:
    """Extract numeric value from budget string."""
    if not budget_str:
        return 1500.0
    import re
    numbers = re.findall(r'[\d,]+\.?\d*', budget_str.replace(',', ''))
    if numbers:
        return float(numbers[0])
    return 1500.0


def parse_travelers(travelers_str: Optional[str]) -> int:
    """Extract number of travelers from string."""
    if not travelers_str:
        return 2
    import re
    numbers = re.findall(r'\d+', travelers_str)
    if numbers:
        return int(numbers[0])
    if any(word in travelers_str.lower() for word in ['solo', 'just me', 'alone', 'myself']):
        return 1
    return 2


def get_destination_key(destination: Optional[str]) -> str:
    """Normalize destination string for DB lookup."""
    if not destination:
        return "default"
    dest_lower = destination.lower().strip()
    for key in ECO_HOTELS_DB.keys():
        if key in dest_lower or dest_lower in key:
            return key
    return "default"


def estimate_distance_km(destination: Optional[str]) -> int:
    """Rough distance estimate from Europe/US hub (in km)."""
    distance_map = {
        "costa rica": 9500,
        "iceland": 1800,
        "new zealand": 18500,
        "japan": 9700,
        "bali": 15000,
        "norway": 1500,
        "switzerland": 1200,
        "canada": 6400,
        "thailand": 10000,
        "portugal": 1600,
        "colombia": 9000,
        "kenya": 6800,
        "peru": 10000,
        "amsterdam": 1050,
        "scotland": 700,
        "morocco": 2200,
        "vietnam": 10200,
        "ecuador": 9800,
        "italy": 1400,
        "barcelona": 1300,
        "australia": 16500,
        "brazil": 9200,
        "nepal": 7800
    }
    if not destination:
        return 3000
    dest_lower = destination.lower()
    for key, dist in distance_map.items():
        if key in dest_lower:
            return dist
    return 3000


def calculate_co2(distance_km: int, transport: str, travelers: int) -> Dict[str, float]:
    """Calculate CO2 emissions in kg for all transport modes."""
    results = {}
    for mode, data in TRANSPORT_DATA.items():
        emissions_kg = data["co2_per_km_per_person"] * distance_km * travelers
        results[mode] = round(emissions_kg, 1)
    return results


def filter_hotels_by_sustainability(hotels: List[Dict], level: str) -> List[Dict]:
    """Filter hotels based on sustainability preference."""
    if level == "high":
        return [h for h in hotels if h["eco_score"] >= 90]
    elif level == "medium":
        return [h for h in hotels if h["eco_score"] >= 75]
    else:
        return hotels


# =============================================================================
# ACTION 1: Recommend Eco-Friendly Hotels
# =============================================================================
class ActionRecommendHotels(Action):

    def name(self) -> Text:
        return "action_recommend_hotels"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        sustainability_level = tracker.get_slot("sustainability_level") or "medium"
        budget = tracker.get_slot("budget")
        budget_value = parse_budget(budget)
        travelers = parse_travelers(tracker.get_slot("travelers"))

        dest_key = get_destination_key(destination)
        hotels = ECO_HOTELS_DB.get(dest_key, ECO_HOTELS_DB["default"])
        filtered = filter_hotels_by_sustainability(hotels, sustainability_level)

        if not filtered:
            filtered = hotels  # fallback to all if filter returns empty

        dest_display = destination if destination else "your destination"

        message = f"🏨 **Eco-Friendly Hotel Recommendations for {dest_display}**\n\n"
        message += f"*(Sustainability preference: {sustainability_level.capitalize()} | Budget: {budget or 'flexible'})*\n\n"

        for i, hotel in enumerate(filtered[:3], 1):
            per_night = hotel['price_per_night']
            stars = "⭐" * hotel['rating']
            certs = " • ".join(hotel['certifications'])
            features = " | ".join(hotel['features'][:3])

            message += f"**{i}. {hotel['name']}** {stars}\n"
            message += f"   💚 Eco Score: {hotel['eco_score']}/100\n"
            message += f"   💵 From ${per_night}/night"
            if travelers > 1:
                message += f" (${per_night * travelers}/night for {travelers} guests)"
            message += f"\n   🏷️ Certifications: {certs}\n"
            message += f"   ✅ Features: {features}\n"
            message += f"   📝 {hotel['description']}\n\n"

        message += "---\n"
        message += "💡 **Eco Tip:** Look for Green Key, Rainforest Alliance, or Gold Standard certifications when booking.\n"
        message += "\nWould you like to know about sustainable transport options or local activities?"

        dispatcher.utter_message(text=message)
        return []


# =============================================================================
# ACTION 2: Recommend Sustainable Transport
# =============================================================================
class ActionRecommendTransport(Action):

    def name(self) -> Text:
        return "action_recommend_transport"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        travelers = parse_travelers(tracker.get_slot("travelers"))
        sustainability_level = tracker.get_slot("sustainability_level") or "medium"
        distance_km = estimate_distance_km(destination)

        dest_display = destination if destination else "your destination"

        # Determine recommended transport based on distance and sustainability
        if distance_km < 800:
            recommended = ["train", "bus", "electric vehicle"]
        elif distance_km < 3000:
            recommended = ["train", "electric vehicle", "bus"]
        else:
            recommended = ["flight", "train"]

        if sustainability_level == "high":
            recommended = sorted(recommended, key=lambda t: TRANSPORT_DATA[t]["co2_per_km_per_person"])

        message = f"🚆 **Sustainable Transport Options to {dest_display}**\n"
        message += f"*(Estimated distance: ~{distance_km:,} km | Travelers: {travelers})*\n\n"

        # Show all transport comparisons
        message += "**📊 Carbon Comparison (round trip):**\n"
        emissions = calculate_co2(distance_km * 2, "", travelers)

        sorted_modes = sorted(emissions.items(), key=lambda x: x[1])
        for mode, co2 in sorted_modes:
            data = TRANSPORT_DATA[mode]
            eco_icon = {"Perfect": "🟢", "High": "🟢", "Medium-High": "🟡",
                        "Medium": "🟡", "Low": "🔴"}.get(data["eco_rating"], "⚪")
            available = "✅" if mode in recommended else ""
            message += f"  {eco_icon} **{mode.title()}**: {co2:.0f} kg CO₂ {available}\n"

        message += "\n**🌱 Our Recommendations:**\n\n"

        for mode in recommended[:3]:
            data = TRANSPORT_DATA[mode]
            co2_total = emissions[mode]
            message += f"**{mode.title()}** — Eco Rating: {data['eco_rating']}\n"
            message += f"   ✅ {' | '.join(data['advantages'][:2])}\n"
            message += f"   💡 Tip: {data['tips']}\n\n"

        message += "---\n"
        message += "🌍 **Did you know?** Train travel can be up to 90% less carbon-intensive than flying on the same route!\n"
        message += "\nWould you like to calculate your exact carbon footprint or see offset programs?"

        dispatcher.utter_message(text=message)
        return []


# =============================================================================
# ACTION 3: Calculate Carbon Emissions
# =============================================================================
class ActionCalculateCarbon(Action):

    def name(self) -> Text:
        return "action_calculate_carbon"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        travelers = parse_travelers(tracker.get_slot("travelers"))
        transport_type = tracker.get_slot("transport_type")
        sustainability_level = tracker.get_slot("sustainability_level") or "medium"

        distance_km = estimate_distance_km(destination)
        round_trip_km = distance_km * 2
        dest_display = destination if destination else "your destination"

        # Calculate emissions for all modes
        all_emissions = calculate_co2(round_trip_km, "", travelers)

        # Primary focus: chosen transport or flight (default for comparison)
        primary_mode = transport_type if transport_type in TRANSPORT_DATA else "flight"
        primary_co2 = all_emissions[primary_mode]

        # Greenest option
        greenest_mode = min(
            {k: v for k, v in all_emissions.items() if k != "cycling"},
            key=lambda k: all_emissions[k]
        )
        greenest_co2 = all_emissions[greenest_mode]
        savings = primary_co2 - greenest_co2

        # Offset cost
        offset_cost = (primary_co2 / 1000) * CARBON_OFFSET_PROGRAMS[0]["price_per_tonne"]

        message = f"🌍 **Carbon Footprint Analysis**\n"
        message += f"**Route:** Home → {dest_display} (Round Trip)\n"
        message += f"**Distance:** ~{round_trip_km:,} km | **Travelers:** {travelers}\n\n"

        message += "**📊 Emissions by Transport Mode:**\n"
        sorted_emissions = sorted(all_emissions.items(), key=lambda x: x[1])
        for mode, co2 in sorted_emissions:
            bar_length = int((co2 / max(all_emissions.values())) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            message += f"  {mode.title():20s} │{bar}│ {co2:,.0f} kg CO₂\n"

        message += f"\n**Your selected transport ({primary_mode.title()}):**\n"
        message += f"  🔴 Total emissions: **{primary_co2:,.0f} kg CO₂** ({travelers} travelers)\n"
        message += f"  👤 Per person: **{primary_co2/travelers:,.0f} kg CO₂**\n"

        message += f"\n**🌱 Greener Alternative ({greenest_mode.title()}):**\n"
        message += f"  🟢 Total emissions: **{greenest_co2:,.0f} kg CO₂**\n"
        if savings > 0:
            message += f"  💚 You would save **{savings:,.0f} kg CO₂** by switching!\n"
            message += f"  🌳 That's equivalent to planting ~{int(savings/21)} trees\n"

        message += f"\n**♻️ Carbon Offset Options:**\n"
        message += f"  To offset {primary_co2:,.0f} kg CO₂:\n"
        for program in CARBON_OFFSET_PROGRAMS[:2]:
            cost = (primary_co2 / 1000) * program["price_per_tonne"]
            message += f"  • **{program['name']}** — ${cost:.2f} ({program['certification']})\n"

        message += "\n**🌡️ Context:**\n"
        message += f"  • Average person's annual footprint: ~7,500 kg CO₂\n"
        message += f"  • This trip = {(primary_co2/7500)*100:.1f}% of annual per-capita footprint\n"

        message += "\n💡 **Eco Tips:**\n"
        message += "  • Pack light — every kg reduces fuel consumption\n"
        message += "  • Choose direct routes when flying\n"
        message += "  • Use public transport at your destination\n"

        dispatcher.utter_message(text=message)
        return []


# =============================================================================
# ACTION 4: Recommend Local Activities
# =============================================================================
class ActionRecommendActivities(Action):

    def name(self) -> Text:
        return "action_recommend_activities"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        sustainability_level = tracker.get_slot("sustainability_level") or "medium"
        travelers = parse_travelers(tracker.get_slot("travelers"))

        dest_key = get_destination_key(destination)
        activities = ACTIVITIES_DB.get(dest_key, ACTIVITIES_DB["default"])
        dest_display = destination if destination else "your destination"

        # Filter by sustainability preference
        if sustainability_level == "high":
            activities = [a for a in activities if a["supports_local"]]
        elif sustainability_level == "medium":
            activities = [a for a in activities if a["carbon_impact"] in ["zero", "minimal"]]

        message = f"🎭 **Eco-Friendly Activities in {dest_display}**\n\n"
        message += f"*(Curated for {sustainability_level.capitalize()} sustainability | {travelers} traveler(s))*\n\n"

        type_icons = {
            "cultural": "🎨",
            "eco-adventure": "🏔️",
            "wildlife": "🦋",
            "natural wonder": "✨",
        }

        for i, activity in enumerate(activities[:6], 1):
            icon = type_icons.get(activity["type"], "🌿")
            cost_total = activity["price"] * travelers
            local_badge = "🏡 Supports Local Community" if activity["supports_local"] else ""

            message += f"**{i}. {icon} {activity['name']}**\n"
            message += f"   Type: {activity['type'].title()} | "
            message += f"Carbon Impact: {activity['carbon_impact'].title()}\n"
            message += f"   💵 ~${activity['price']}/person"
            if travelers > 1:
                message += f" (${cost_total} for {travelers})"
            message += "\n"
            if local_badge:
                message += f"   {local_badge}\n"
            message += "\n"

        message += "---\n"
        message += "♻️ **Carbon Offset Opportunities at Destination:**\n"
        message += "  • Participate in local reforestation programs\n"
        message += "  • Support conservation projects directly\n"
        message += "  • Volunteer with local environmental NGOs\n\n"

        message += "💡 **Responsible Travel Tips:**\n"
        message += "  • Always hire certified local guides\n"
        message += "  • Buy directly from local artisans\n"
        message += "  • Respect local customs and sacred sites\n"
        message += "  • Leave no trace — pack out what you pack in\n"

        dispatcher.utter_message(text=message)
        return []


# =============================================================================
# ACTION 5: Human Handover
# =============================================================================
class ActionHumanHandover(Action):

    def name(self) -> Text:
        return "action_human_handover"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        budget = tracker.get_slot("budget")
        travel_date = tracker.get_slot("travel_date")
        travelers = tracker.get_slot("travelers")
        sustainability_level = tracker.get_slot("sustainability_level")

        # Build summary for human agent
        summary_lines = []
        if destination:
            summary_lines.append(f"Destination: {destination}")
        if travel_date:
            summary_lines.append(f"Travel Dates: {travel_date}")
        if budget:
            summary_lines.append(f"Budget: {budget}")
        if travelers:
            summary_lines.append(f"Travelers: {travelers}")
        if sustainability_level:
            summary_lines.append(f"Sustainability Preference: {sustainability_level.capitalize()}")

        # Last user messages context
        last_messages = []
        for event in reversed(tracker.events):
            if event.get("event") == "user" and len(last_messages) < 3:
                last_messages.insert(0, event.get("text", ""))

        message = "👤 **Initiating Human Agent Transfer**\n\n"
        message += "I'm connecting you to a certified eco-travel specialist who can provide personalized assistance.\n\n"

        message += "**📋 Conversation Summary (shared with agent):**\n"
        if summary_lines:
            for line in summary_lines:
                message += f"  • {line}\n"
        else:
            message += "  • No trip details collected yet\n"

        message += "\n**Recent conversation context has been shared.**\n\n"
        message += "⏳ **Estimated wait time:** 2-5 minutes\n"
        message += "📧 **Alternative:** If no agent is available, we'll email you within 24 hours.\n\n"
        message += "Thank you for choosing eco-friendly travel! 🌿"

        dispatcher.utter_message(text=message)

        # In production: trigger actual handover event
        # This pauses the Rasa bot and hands control to a human agent system
        return [
            SlotSet("handover_requested", True),
            ConversationPaused()
        ]


# =============================================================================
# ACTION 6: Trip Summary
# =============================================================================
class ActionTripSummary(Action):

    def name(self) -> Text:
        return "action_trip_summary"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:

        destination = tracker.get_slot("destination")
        budget = tracker.get_slot("budget")
        travel_date = tracker.get_slot("travel_date")
        travelers_str = tracker.get_slot("travelers")
        sustainability_level = tracker.get_slot("sustainability_level") or "medium"

        travelers = parse_travelers(travelers_str)
        budget_value = parse_budget(budget)
        distance_km = estimate_distance_km(destination)

        # Estimate emissions for best transport
        emissions = calculate_co2(distance_km * 2, "", travelers)
        greenest_mode = min(
            {k: v for k, v in emissions.items() if k != "cycling"},
            key=lambda k: emissions[k]
        )

        # Eco score calculation
        level_scores = {"high": 95, "medium": 75, "low": 55}
        eco_score = level_scores.get(sustainability_level, 75)

        sustainability_icons = {"high": "🟢", "medium": "🟡", "low": "🔴"}
        eco_icon = sustainability_icons.get(sustainability_level, "🟡")

        message = "✅ **Your Eco-Travel Summary**\n"
        message += "=" * 40 + "\n\n"

        message += f"🗺️  **Destination:** {destination or 'Not specified'}\n"
        message += f"📅  **Travel Dates:** {travel_date or 'Not specified'}\n"
        message += f"💰  **Budget:** {budget or 'Not specified'}\n"
        message += f"👥  **Travelers:** {travelers_str or 'Not specified'}\n"
        message += f"{eco_icon}  **Sustainability Level:** {sustainability_level.capitalize()}\n\n"

        message += "**🌿 Eco Impact Preview:**\n"
        message += f"  • Recommended transport: {greenest_mode.title()}\n"
        message += f"  • Estimated emissions (RT): {emissions[greenest_mode]:,.0f} kg CO₂\n"
        message += f"  • Your Eco Score: {eco_score}/100\n\n"

        message += "**📌 What's next?**\n"
        message += "  🏨 Type **'show hotels'** for eco accommodation\n"
        message += "  🚆 Type **'transport options'** for green travel\n"
        message += "  🌍 Type **'carbon footprint'** for detailed emissions\n"
        message += "  🎭 Type **'activities'** for local cultural experiences\n"
        message += "  👤 Type **'human agent'** to speak with a specialist\n"

        dispatcher.utter_message(text=message)
        return []


# =============================================================================
# ACTION 7: Form Validation
# =============================================================================
class ValidateTripPlanningForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_trip_planning_form"

    def validate_destination(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate destination is a non-empty string."""
        if not slot_value or len(str(slot_value).strip()) < 2:
            dispatcher.utter_message(
                text="❌ Please provide a valid destination (city or country)."
            )
            return {"destination": None}

        destination = str(slot_value).strip().title()
        dispatcher.utter_message(
            text=f"✅ Great choice! **{destination}** is a wonderful destination."
        )
        return {"destination": destination}

    def validate_budget(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate budget input."""
        if not slot_value:
            dispatcher.utter_message(
                text="❌ Please provide your budget (e.g., $1000, 2000 USD, or 'medium budget')."
            )
            return {"budget": None}

        budget_str = str(slot_value).strip()
        budget_value = parse_budget(budget_str)

        if budget_value < 100:
            dispatcher.utter_message(
                text="⚠️ That's a very tight budget for eco-travel. We'll find the most affordable sustainable options for you!"
            )
        elif budget_value > 10000:
            dispatcher.utter_message(
                text="✅ Excellent! With a generous budget, we can find the finest eco-luxury experiences!"
            )
        else:
            dispatcher.utter_message(
                text=f"✅ Budget of **{budget_str}** noted. I'll find great eco-friendly options in your range."
            )

        return {"budget": budget_str}

    def validate_travel_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate travel dates."""
        if not slot_value or len(str(slot_value).strip()) < 2:
            dispatcher.utter_message(
                text="❌ Please provide travel dates (e.g., 'July 15-22' or 'next summer')."
            )
            return {"travel_date": None}

        dispatcher.utter_message(
            text=f"✅ Travel dates **{slot_value}** noted."
        )
        return {"travel_date": str(slot_value).strip()}

    def validate_travelers(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate number of travelers."""
        if not slot_value:
            dispatcher.utter_message(text="❌ Please tell me how many people will be traveling.")
            return {"travelers": None}

        travelers_str = str(slot_value).strip()
        count = parse_travelers(travelers_str)

        if count < 1:
            dispatcher.utter_message(
                text="❌ Please enter at least 1 traveler."
            )
            return {"travelers": None}

        if count > 50:
            dispatcher.utter_message(
                text="⚠️ That's a large group! For groups over 50, I recommend contacting a specialist directly."
            )
        elif count == 1:
            dispatcher.utter_message(text="✅ Solo travel noted! We have great eco-options for solo adventurers.")
        else:
            dispatcher.utter_message(text=f"✅ Got it — **{count} travelers**.")

        return {"travelers": travelers_str}

    def validate_sustainability_level(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate sustainability preference is low/medium/high."""
        if not slot_value:
            dispatcher.utter_message(
                text="Please choose: **Low**, **Medium**, or **High** sustainability."
            )
            return {"sustainability_level": None}

        value_lower = str(slot_value).lower().strip()

        # Map synonyms
        high_synonyms = ["high", "maximum", "max", "very high", "fully sustainable", "green", "fully green"]
        medium_synonyms = ["medium", "moderate", "balanced", "somewhat", "average", "mixed"]
        low_synonyms = ["low", "minimal", "basic", "not much", "low priority"]

        if any(syn in value_lower for syn in high_synonyms):
            level = "high"
            dispatcher.utter_message(
                text="🟢 **High sustainability** selected — I'll prioritize the most eco-friendly options!"
            )
        elif any(syn in value_lower for syn in medium_synonyms):
            level = "medium"
            dispatcher.utter_message(
                text="🟡 **Medium sustainability** selected — a great balance of comfort and eco-responsibility."
            )
        elif any(syn in value_lower for syn in low_synonyms):
            level = "low"
            dispatcher.utter_message(
                text="🔵 **Low sustainability** noted — I'll still suggest eco-friendly alternatives where possible."
            )
        else:
            dispatcher.utter_message(
                text="❌ Please choose one of: **Low**, **Medium**, or **High** sustainability preference."
            )
            return {"sustainability_level": None}

        return {"sustainability_level": level}

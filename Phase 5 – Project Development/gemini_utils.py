import json
import os
from urllib.parse import quote_plus

try:
    from google import genai
    from PIL import Image
except ImportError:
    genai = None
    Image = None

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
API_KEY = os.getenv("GEMINI_API_KEY")


def platform_links(search_term, platforms):
    q = quote_plus(search_term or "")
    base = {
        "Amazon": f"https://www.amazon.in/s?k={q}",
        "Flipkart": f"https://www.flipkart.com/search?q={q}",
        "IKEA": f"https://www.ikea.com/in/en/search/?q={q}",
        "Myntra": f"https://www.myntra.com/{q.replace('+', '-')}",
        "Swiggy": f"https://www.swiggy.com/search?query={q}",
        "Zomato": f"https://www.zomato.com/search?query={q}",
        "Booking": f"https://www.booking.com/searchresults.html?ss={q}",
        "OYO": f"https://www.oyorooms.com/search?location={q}",
    }
    return {p: base[p] for p in platforms if p in base}


def extract_json(text):
    if not text:
        return None
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None


def call_gemini(prompt, image_path=None):
    """Live Gemini call. Any API/quota problem falls back to demo mode."""
    if not API_KEY or genai is None:
        return None
    try:
        client = genai.Client(api_key=API_KEY)
        contents = [prompt]
        if image_path and Image:
            contents.append(Image.open(image_path))
        response = client.models.generate_content(model=MODEL_NAME, contents=contents)
        return extract_json(response.text)
    except Exception:
        return None


def _home_demo(data):
    budget = data["total_budget"]
    lighting = round(budget * 0.30)
    fans = round(budget * 0.20)
    furniture = round(budget * 0.30)
    decor = max(round(budget - lighting - fans - furniture), 0)
    return {
        "title": "Your Personalized Home Budget Plan",
        "mode_note": "Demo recommendation shown because Gemini quota/API is temporarily unavailable.",
        "budget_summary": {"total": budget, "remaining": 0},
        "budget_breakdown": [
            {"category": "Lighting", "allocation": lighting, "items": [{"name": "LED Bulb (Warm White)", "description": "Energy-efficient LED bulbs for general lighting.", "estimated_price": 100, "quantity": max(data["num_lights"], 1), "search_terms": "LED bulb warm white"}]},
            {"category": "Ceiling Fans", "allocation": fans, "items": [{"name": "Havells Ceiling Fan", "description": "Basic, functional ceiling fan.", "estimated_price": 500, "quantity": max(data["num_fans"], 1), "search_terms": "Havells ceiling fan"}]},
            {"category": "Furniture", "allocation": furniture, "items": [
                {"name": "Plastic Chair", "description": "Stackable plastic chairs for kitchen or living room.", "estimated_price": 250, "quantity": max(data["num_furniture"], 1), "search_terms": "plastic chair"},
                {"name": "Small Wooden Table", "description": "Simple wooden table for dining or side use.", "estimated_price": 500, "quantity": max(data["num_dining_tables"], 1), "search_terms": "small wooden dining table"},
            ]},
            {"category": "Decor", "allocation": decor, "items": [{"name": "Wall Decor", "description": "Affordable decorative items for a clean modern look.", "estimated_price": 1500, "quantity": 1, "search_terms": "home wall decor"}]},
        ],
        "remaining_budget": 0,
        "tips": [
            "Consider purchasing used furniture for further cost savings.",
            "Look for sales and discounts on online marketplaces.",
            "Prioritize essential items and postpone non-essential purchases.",
        ],
    }


def _party_demo(data):
    budget = data["total_budget"]
    venue = 0 if data["venue_type"].lower() == "home" else round(budget * 0.10)
    catering = round(budget * 0.40) if data["needs_catering"] else 0
    decoration = round(budget * 0.15) if data["needs_decoration"] else 0
    entertainment = round(budget * 0.25) if data["needs_entertainment"] else 0
    contingency = max(budget - (venue + catering + decoration + entertainment), 0)
    return {
        "title": "Your Party Budget Plan",
        "mode_note": "Demo recommendation shown because Gemini quota/API is temporarily unavailable.",
        "budget_breakdown": [
            {"category": "Venue", "allocation": venue, "items": [{"name": data["venue_type"] or "Home", "description": "Venue arrangement for the event.", "estimated_price": venue, "quantity": 1, "search_terms": data["venue_type"] or "party venue"}]},
            {"category": "Catering", "allocation": catering, "items": [{"name": "Home-cooked meal", "description": f"Simple meal plan for {data['num_guests']} guests.", "estimated_price": catering, "quantity": 1, "search_terms": "party catering"}]},
            {"category": "Entertainment", "allocation": entertainment, "items": [
                {"name": "Streaming service subscription", "description": "Short-term entertainment subscription for the event.", "estimated_price": round(entertainment * 0.25), "quantity": 1, "search_terms": "streaming service subscription"},
                {"name": "Board games/cards", "description": "Fun group games for guests.", "estimated_price": round(entertainment * 0.25), "quantity": 1, "search_terms": "board games cards"},
                {"name": "Music playlist", "description": "Create a celebration playlist.", "estimated_price": 0, "quantity": 1, "search_terms": "party speaker"},
                {"name": "Small gift for couple", "description": "A small appreciation gift.", "estimated_price": max(round(entertainment * 0.50), 0), "quantity": 1, "search_terms": "wedding gift"},
            ]},
            {"category": "Contingency", "allocation": contingency, "items": [{"name": "Unexpected expenses", "description": "Buffer for unforeseen costs.", "estimated_price": contingency, "quantity": 1, "search_terms": "event supplies"}]},
        ],
        "remaining_budget": 0,
        "tips": [
            "Consider making the meal a potluck style if comfortable with guests to reduce catering costs.",
            "Look for discounts or offers on entertainment and party supplies.",
            "Homemade decorations can be a cost-effective alternative.",
        ],
    }


def _jewelry_demo(data):
    first = min(500, data["total_budget"])
    second = min(700, max(data["total_budget"] - first, 0))
    third = min(300, max(data["total_budget"] - first - second, 0))
    used = first + second + third
    return {
        "title": "Your Personalized Jewelry Recommendations",
        "mode_note": "Demo recommendation shown because Gemini quota/API is temporarily unavailable.",
        "budget_summary": {"total": data["total_budget"], "remaining": max(data["total_budget"] - used, 0)},
        "outfit_analysis": {"colors": "Blue, white", "style": "Casual", "formality": "Informal"},
        "jewelry_recommendations": [
            {"item_type": "bracelet", "description": "A simple braided leather bracelet with metal accents. This complements a casual outfit without being overly flashy.", "style": "casual", "estimated_price": first, "search_terms": "casual bracelet"},
            {"item_type": "ring", "description": "A silver or dark grey metal ring with a minimalist design. Avoid anything too large or ostentatious.", "style": "minimalist", "estimated_price": second, "search_terms": "minimalist silver ring"},
            {"item_type": "watch", "description": "A classic simple watch with a leather or metal band. A darker band complements shirt colors.", "style": "classic", "estimated_price": third, "search_terms": "classic watch"},
        ],
        "remaining_budget": max(data["total_budget"] - used, 0),
        "styling_tips": [
            "Keep the jewelry minimal to match the casual style of the outfit.",
            "Consider a watch as a statement piece that reflects personal style.",
            "Ensure the metal tones of the ring and bracelet complement each other.",
        ],
    }


def _add_links(result, platforms):
    for category in result.get("budget_breakdown", []):
        for item in category.get("items", []):
            item["shopping_links"] = platform_links(item.get("search_terms") or item.get("name", ""), platforms)
    for item in result.get("jewelry_recommendations", []):
        item["shopping_links"] = platform_links(item.get("search_terms") or item.get("item_type", ""), platforms)
    return result


def generate_home_recommendations(data):
    prompt = f"""
You are PocketSmart AI, a budget recommendation assistant for users in India.
Create practical home interior recommendations using INR prices.
Budget: ₹{data['total_budget']:.0f}
Rooms: {', '.join(data['rooms']) or 'Not specified'}
Lights: {data['num_lights']}; Fans: {data['num_fans']}; Furniture: {data['num_furniture']}; Dining tables: {data['num_dining_tables']}
Additional requirements: {data['additional_requirements'] or 'None'}
Return ONLY JSON with title, budget_summary, budget_breakdown, remaining_budget, tips.
Each category has category, allocation, items. Each item has name, description, estimated_price, quantity, search_terms.
Keep the estimated total within the budget.
"""
    result = call_gemini(prompt)
    return _add_links(result, ["Amazon", "Flipkart", "IKEA", "Myntra"]) if result else _add_links(_home_demo(data), ["Amazon", "Flipkart", "IKEA", "Myntra"])


def generate_party_recommendations(data):
    prompt = f"""
You are PocketSmart AI for party planning in India.
Budget: ₹{data['total_budget']:.0f}; Event: {data['party_type']}; Guests: {data['num_guests']}; Venue: {data['venue_type']}
Catering: {'Yes' if data['needs_catering'] else 'No'}; Decoration: {'Yes' if data['needs_decoration'] else 'No'}; Entertainment: {'Yes' if data['needs_entertainment'] else 'No'}
Additional requirements: {data['additional_requirements'] or 'None'}
Return ONLY JSON with title, budget_breakdown, remaining_budget, tips.
Each category has category, allocation, items. Each item has name, description, estimated_price, quantity, search_terms.
Keep the total within budget.
"""
    result = call_gemini(prompt)
    return _add_links(result, ["Amazon", "Flipkart", "Swiggy", "Zomato", "Booking", "OYO"]) if result else _add_links(_party_demo(data), ["Amazon", "Flipkart", "Swiggy", "Zomato", "Booking", "OYO"])


def generate_jewelry_recommendations(data, image_path=None):
    prompt = f"""
You are PocketSmart AI, a jewelry recommendation assistant for India.
Budget: ₹{data['total_budget']:.0f}; Occasion: {data['occasion']}; Style: {data['style']}
Additional requirements: {data['additional_requirements'] or 'None'}
If an outfit image is provided, consider visible colors and style.
Return ONLY JSON with title, budget_summary, outfit_analysis, jewelry_recommendations, remaining_budget, styling_tips.
Each jewelry recommendation has item_type, description, style, estimated_price, search_terms.
Keep recommendations within budget.
"""
    result = call_gemini(prompt, image_path)
    return _add_links(result, ["Amazon", "Flipkart", "Myntra"]) if result else _add_links(_jewelry_demo(data), ["Amazon", "Flipkart", "Myntra"])

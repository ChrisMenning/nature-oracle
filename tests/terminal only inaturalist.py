import requests
from datetime import datetime, timedelta
from collections import defaultdict
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk

# === CONFIGURATION ===
latitude = 44.5161
longitude = -88.0903
days_back = 7
radius_km = 10
max_results = 20
text_display_time = 3   # seconds
image_display_time = 3  # seconds
screen_width, screen_height = 240, 280

# === DATE RANGE ===
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# === TAXON CACHE ===
taxon_cache = {}

def get_taxon_names(taxon_id):
    if taxon_id in taxon_cache:
        return taxon_cache[taxon_id]
    taxon_url = f"https://api.inaturalist.org/v1/taxa/{taxon_id}"
    r = requests.get(taxon_url)
    if r.status_code == 200:
        tdata = r.json().get("results", [])
        if tdata:
            taxon = tdata[0]
            sci_name = taxon.get("name", "Unknown")
            common_names = [n.get("name") for n in taxon.get("common_names", []) if n.get("name")]
            preferred_common = taxon.get("preferred_common_name")
            if preferred_common and preferred_common not in common_names:
                common_names.insert(0, preferred_common)
            taxon_cache[taxon_id] = (sci_name, common_names)
            return sci_name, common_names
    taxon_cache[taxon_id] = ("Unknown", [])
    return "Unknown", []

# === FETCH OBSERVATIONS ===
obs_url = "https://api.inaturalist.org/v1/observations"
obs_params = {
    "lat": latitude,
    "lng": longitude,
    "radius": radius_km,
    "d1": start_date_str,
    "d2": end_date_str,
    "per_page": max_results,
    "order_by": "observed_on",
    "order": "desc"
}

resp = requests.get(obs_url, params=obs_params)
data = resp.json().get("results", [])

if not data:
    slides = [{"text": "No recent observations found."}]
else:
    grouped = defaultdict(list)
    for obs in data:
        taxon = obs.get("taxon")
        if not taxon:
            continue
        taxon_id = taxon["id"]
        iconic = taxon.get("iconic_taxon_name", "Other")
        obs_date = obs.get("observed_on", "Unknown date")
        # Format date as Month Day
        try:
            obs_date = datetime.strptime(obs_date, "%Y-%m-%d").strftime("%b %d")
        except Exception:
            obs_date = "Unknown Date"

        sci_name, common_names = get_taxon_names(taxon_id)
        photo_url = None
        if obs.get("photos"):
            photo_url = obs["photos"][0]["url"].replace("square", "medium")

        grouped[iconic].append({
            "scientific_name": sci_name,
            "common_names": common_names,
            "date": obs_date,
            "photo_url": photo_url
        })

    # Prepare slides: intro + taxon summary + observations
    slides = [{"text": "Recent biological sightings within 10 km"}]
    for iconic_group, species_list in grouped.items():
        slides.append({"text": f"{iconic_group} ({len(species_list)} observations)"})
        for s in species_list:
            names = f" ({', '.join(s['common_names'])})" if s['common_names'] else ""
            slides.append({"text": f"{s['scientific_name']}{names} observed on {s['date']}"})
            # Append image slide if available
            if s.get("photo_url"):
                slides.append({"image_url": s["photo_url"]})

# === SLIDESHOW ===
class Slideshow:
    def __init__(self, slides):
        self.slides = slides
        self.index = 0
        self.root = tk.Tk()
        self.root.title("iNaturalist Slideshow")
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.label = tk.Label(self.root, bg="black", fg="white", wraplength=screen_width, font=("Helvetica", 14))
        self.label.pack(expand=True, fill="both")
        self.show_slide()
        self.root.mainloop()

    def show_slide(self):
        slide = self.slides[self.index]

        if "text" in slide:
            self.label.config(text=slide["text"], image="")
            delay = text_display_time * 1000
        elif "image_url" in slide:
            try:
                img_data = requests.get(slide["image_url"]).content
                img = Image.open(BytesIO(img_data))
                img = img.resize((screen_width, screen_height))
                photo = ImageTk.PhotoImage(img)
                self.label.config(image=photo, text="")
                self.label.image = photo
            except Exception:
                self.label.config(text="Image failed to load", image="")
            delay = image_display_time * 1000

        self.index = (self.index + 1) % len(self.slides)
        self.root.after(delay, self.show_slide)

if __name__ == "__main__":
    Slideshow(slides)

import matplotlib
matplotlib.use('Agg')

import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
from tqdm import tqdm
import os
from django.conf import settings

# API call to get a page of identifications
def get_obs(user, max_id):
    url = f"https://api.inaturalist.org/v1/identifications?current=any&user_id={user}&per_page=200&order_by=id&order=asc&id_above={max_id}"
    response = requests.get(url)
    print(response)
    results = response.json().get("results", [])
    return pd.json_normalize(results)

# Fetch all identifications using pagination
def fetch_all_obs(user):
    all_data = []
    max_id = 0
    with tqdm(total=1, desc="Fetching pages") as pbar:
        while True:
            obs = get_obs(user, max_id)
            if obs.empty:
                break
            all_data.append(obs)
            max_id = obs["id"].max()
            if len(obs) < 200:
                break
            pbar.update(1)
    if not all_data:
        print("No data found for this user.")
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)

# Prepare and clean the raw data
def prepare_data(data):
    data = data[data["own_observation"] == False]
    inatid = data.loc[:, [
        'id', 'created_at_details.date', 'taxon_id',
        'observation.taxon.preferred_common_name', 'observation.taxon.name',
        'observation.taxon.iconic_taxon_name', 'observation.taxon.default_photo.medium_url',
        'observation.taxon.default_photo.attribution', 'observation.geojson.coordinates',
        'observation.user.login', 'observation.observed_time_zone'
    ]].rename(columns={
        'created_at_details.date': 'id_date',
        'observation.taxon.preferred_common_name': 'species',
        'observation.taxon.name': 'scientific_name',
        'observation.taxon.iconic_taxon_name': 'taxon',
        'observation.taxon.default_photo.medium_url': 'photourl',
        'observation.taxon.default_photo.attribution': 'photo_attribution',
        'observation.geojson.coordinates': 'coords',
        'observation.user.login': 'ob_user_id',
        'observation.observed_time_zone': 'region'
    })

    inatid["id_date"] = pd.to_datetime(inatid["id_date"])
    inatid["count"] = 1
    return inatid

# Plot cumulative identifications over time
def plot_identifications(inatid, username):
    inatid["year"] = inatid["id_date"].dt.isocalendar().year
    inatid["week"] = inatid["id_date"].dt.isocalendar().week

    weekly_stats = (
        inatid.groupby(["year", "week"], sort=True, as_index=False)
        .agg(id_per_week=("count", "sum"), id_date_middle=("id_date", "median"))
    )
    weekly_stats["cum_id_week"] = np.cumsum(weekly_stats["id_per_week"])

    plot_path = os.path.join(settings.MEDIA_ROOT, f"{username}_identifications_overtime.png")
    plt.figure(figsize=(10, 5))
    sns.lineplot(x="id_date_middle", y="cum_id_week", data=weekly_stats, linewidth=2)
    plt.fill_between(weekly_stats["id_date_middle"], weekly_stats["cum_id_week"], alpha=0.3)
    plt.ylabel("Number of Identifications")
    plt.title("Cumulative Identifications Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()
    return settings.MEDIA_URL + username + "_identifications_overtime.png"

# Plot cumulative unique users over time
def plot_users(inatid, username):
    user_first = (
        inatid.groupby("ob_user_id", as_index=False)
        .agg(first_appearance=("id_date", "min"))
    )
    user_first["year"] = user_first["first_appearance"].dt.isocalendar().year
    user_first["week"] = user_first["first_appearance"].dt.isocalendar().week

    new_users_week = (
        user_first.groupby(["year", "week"], as_index=False)
        .size().rename(columns={"size": "new_users"})
    )

    start_of_year = pd.to_datetime(new_users_week["year"].astype(str) + "-01-01")
    new_users_week["id_date_middle"] = start_of_year + pd.to_timedelta((new_users_week["week"] - 1) * 7, unit="D")
    new_users_week["cum_users"] = np.cumsum(new_users_week["new_users"])

    plot_path = os.path.join(settings.MEDIA_ROOT, f"{username}_identifications_for_users_overtime.png")
    plt.figure(figsize=(10, 5))
    sns.lineplot(x="id_date_middle", y="cum_users", data=new_users_week, color="blue", linewidth=2)
    plt.fill_between(new_users_week["id_date_middle"], new_users_week["cum_users"], color="blue", alpha=0.3)
    plt.ylabel("Number of Individuals")
    plt.title("Cumulative Unique Users Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(plot_path, transparent=True)
    plt.close()
    return settings.MEDIA_URL + username + "_identifications_for_users_overtime.png"

# Estimate geographic coverage in acres
def calculate_coverage(inatid):
    valid_coords = inatid["coords"].apply(lambda x: isinstance(x, list) and len(x) == 2 and all(isinstance(i, (int, float)) for i in x))
    inatid_valid = inatid[valid_coords].copy()

    coords_array = np.array(inatid_valid["coords"].tolist())
    coords_df = pd.DataFrame(coords_array, columns=["lon", "lat"])

    geometry = [Point(xy) for xy in zip(coords_df["lon"], coords_df["lat"])]
    inat_gdf = gpd.GeoDataFrame(coords_df, geometry=geometry, crs="EPSG:4326").to_crs(epsg=6933)

    acre_area_m2 = 4046.86
    radius_m = np.sqrt(acre_area_m2 / np.pi)
    inat_gdf["buffer"] = inat_gdf["geometry"].buffer(radius_m)

    total_area_m2 = inat_gdf["buffer"].union_all().area
    unique_acres = total_area_m2 / acre_area_m2
    return unique_acres

# Main function to run the entire workflow
def process_username(user):
    print(f"\nFetching iNaturalist identifications for user: {user}\n")
    raw_data = fetch_all_obs(user)
    if raw_data.empty:
        return {
            "error": "No data found for the given username.",
            "username": user
        }
    inatid = prepare_data(raw_data)

    total_ids = len(inatid)
    unique_users = inatid["ob_user_id"].nunique()
    volunteer_hours = total_ids // 30

    id_plot_url = plot_identifications(inatid, username=user)
    user_plot_url = plot_users(inatid, username=user)
    unique_acres = calculate_coverage(inatid)

    # Schedule deletion of generated graph images after rendering
    def delete_images():
        os.remove(os.path.join(settings.MEDIA_ROOT, f"{user}_identifications_overtime.png"))
        os.remove(os.path.join(settings.MEDIA_ROOT, f"{user}_identifications_for_users_overtime.png"))

    from threading import Timer
    Timer(5.0, delete_images).start()

    return {
        "total_ids": total_ids,
        "unique_users": unique_users,
        "volunteer_hours": volunteer_hours,
        "estimated_coverage_acres": round(unique_acres),
        "id_plot_url": id_plot_url,
        "user_plot_url": user_plot_url
    }

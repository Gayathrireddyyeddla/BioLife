# bioblitz_service.py

import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from django.conf import settings


def process_projectslug(project_slug):
    media_dir = os.path.join(settings.MEDIA_ROOT, 'bioblitz', project_slug)
    os.makedirs(media_dir, exist_ok=True)

    # Total Observations
    obs_response = requests.get(f"https://api.inaturalist.org/v1/observations?project_id={project_slug}&per_page=0")

    if obs_response.status_code != 200:
        print(f"Error fetching data for project {project_slug}: {obs_response.status_code}")
        return {"error": "Failed to fetch data from iNaturalist API."}
    total_observations = obs_response.json()['total_results']
    print(f"Total Observations: {total_observations}")

    # Observers
    all_observers = []
    page, per_page = 1, 200
    while True:
        url = f"https://api.inaturalist.org/v1/observations/observers?project_id={project_slug}&page={page}&per_page={per_page}"
        data = requests.get(url).json()
        if not data['results']:
            break
        all_observers.extend(data['results'])
        if len(data['results']) < per_page:
            break
        page += 1
    observers_df = pd.DataFrame(all_observers)
    total_observers = observers_df['user_id'].nunique()

    # Species
    species_response = requests.get(f"https://api.inaturalist.org/v1/observations/species_counts?project_id={project_slug}")
    total_species = species_response.json()['total_results']

    # Project Place
    project_response = requests.get(f"https://api.inaturalist.org/v1/projects/{project_slug}")
    place_id = project_response.json()['results'][0]['place_id']

    # Start and End Dates
    start_date = pd.to_datetime(requests.get(
        f"https://api.inaturalist.org/v1/observations?project_id={project_slug}&order=asc&order_by=observed_on&per_page=1"
    ).json()['results'][0]['observed_on']).date()

    end_date = pd.to_datetime(requests.get(
        f"https://api.inaturalist.org/v1/observations?project_id={project_slug}&order=desc&order_by=observed_on&per_page=1"
    ).json()['results'][0]['observed_on']).date()

    # Place Observations
    obs_data_place = requests.get(
        f"https://api.inaturalist.org/v1/observations?place_id={place_id}&d2={start_date - timedelta(days=1)}&per_page=0"
    ).json()
    total_observations_place = obs_data_place['total_results']

    # Place Observers
    all_observers_place = []
    page = 1
    while True:
        url = f"https://api.inaturalist.org/v1/observations/observers?place_id={place_id}&d2={start_date - timedelta(days=1)}&page={page}&per_page={per_page}"
        data = requests.get(url).json()
        if not data['results']:
            break
        all_observers_place.extend(data['results'])
        if len(data['results']) < per_page:
            break
        page += 1
    observers_df_place = pd.DataFrame(all_observers_place)
    total_observers_place = observers_df_place['user_id'].nunique()

    # Place Species
    total_species_place = requests.get(
        f"https://api.inaturalist.org/v1/observations/species_counts?place_id={place_id}&d2={start_date - timedelta(days=1)}"
    ).json()['total_results']

    # Calculate increases
    user_increase_percent = round(((total_observers + total_observers_place) - total_observers_place) / total_observers_place * 100, 2)
    obs_increase_percent = round((total_observations_place - total_observations) / total_observations * 100, 2)
    species_increase_percent = round((total_species + total_species_place - total_species_place) / total_species_place * 100, 2)

    # Observation Bar Chart
    plt.figure(figsize=(6, 3.5))
    plt.bar(['Before Bioblitz', 'After Bioblitz'], [total_observations, total_observations_place])
    plt.ylabel('Number of Observations')
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()
    obs_graph_path = os.path.join(media_dir, 'project_observations.png')
    plt.savefig(obs_graph_path, transparent=True)
    plt.close()

    # Species Bar Chart
    plt.figure(figsize=(6, 3.5))
    plt.bar(['Before Bioblitz', 'After Bioblitz'], [total_species_place, total_species + total_species_place])
    plt.ylabel('Number of Species')
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.tight_layout()
    species_graph_path = os.path.join(media_dir, 'project_species.png')
    plt.savefig(species_graph_path, transparent=True)
    plt.close()

    # New Users
    observers_df['user_creation'] = pd.to_datetime(observers_df['user'].apply(lambda x: x['created_at'])).dt.tz_localize(None).dt.date
    new_users_df = observers_df[(observers_df['user_creation'] >= start_date) & (observers_df['user_creation'] <= end_date)]
    new_users_count = len(new_users_df)
    new_users_percent = round((new_users_count / len(observers_df)) * 100, 2)

    # Convert graph paths to URLs using proper URL concatenation
    obs_graph_url = f"{settings.MEDIA_URL}bioblitz/{project_slug}/project_observations.png"
    species_graph_url = f"{settings.MEDIA_URL}bioblitz/{project_slug}/project_species.png"

    # Schedule deletion of generated graph images and subfolder after rendering
    def delete_images_and_folder():
        os.remove(os.path.join(media_dir, 'project_observations.png'))
        os.remove(os.path.join(media_dir, 'project_species.png'))
        os.rmdir(media_dir)  # Remove the subfolder for the project_slug

    from threading import Timer
    Timer(5.0, delete_images_and_folder).start()

    return {
        "project_slug": project_slug,
        "graph_paths": [obs_graph_url, species_graph_url],
        "total_observations_place": total_observations_place,
        "Place_Total_Observation": total_observations_place,
        "Place_Total_Observers": total_observers_place,
        "Place_Total_Species": total_species_place,
        "User_Increase_Percent": user_increase_percent,
        "Observation_Increase_Percent": obs_increase_percent,
        "Species_Increase_Percent": species_increase_percent,
        "New_Users": new_users_count,
        "New_Users_Percentage": new_users_percent
    }

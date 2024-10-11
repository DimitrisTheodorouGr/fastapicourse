from fastapi import Depends, APIRouter, Form, File, UploadFile
import os
import xml.etree.ElementTree as ET
import requests

router = APIRouter(
    prefix='/kml',
    tags=['kml']
)

# API endpoint for the wellness project
api_url = "https://project-wellness.ece.uowm.gr/wellness-api/collar/data/"

@router.post("/upload_kml/")
async def upload_kml(collar_id: int = Form(...), file: UploadFile = File(...)):
    # Save uploaded file temporarily
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Process the KML file and send API requests
    process_kml(file_location, collar_id)

    # Delete the temp file after processing
    os.remove(file_location)

    return {"status": "File processed successfully", "collar_id": collar_id}

def process_kml(kml_file: str, collar_id: int):
    # Load and parse the KML file
    tree = ET.parse(kml_file)
    root = tree.getroot()

    # Namespace for KML
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    # Iterate through each Placemark
    for placemark in root.findall(".//kml:Placemark", namespace):
        # Extract coordinates and timestamp
        coordinates = placemark.find(".//kml:Point/kml:coordinates", namespace)
        when = placemark.find(".//kml:TimeStamp/kml:when", namespace)

        if coordinates is not None and when is not None:
            coord_text = coordinates.text.strip()
            longitude, latitude, altitude = map(float, coord_text.split(","))
            timestamp = when.text

            # Prepare the API request body
            payload = {
                "collar_id": collar_id,
                "latitude": latitude,
                "longitude": longitude,
                "temperature": 0,
                "battery_percentage": 0,
                "altitude": altitude,
                "humidity": 0,
                "timestamp": timestamp
            }

            # Send the POST request
            response = requests.post(api_url, json=payload)

            # Log the response status
            if response.status_code == 200:
                print(f"Success: Sent data for {latitude}, {longitude} at {timestamp}")
            else:
                print(f"Failed: {response.status_code} for {latitude}, {longitude}")

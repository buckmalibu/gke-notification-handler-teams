#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : github.com/echoboomer (https://github.com/echoboomer/gke-notification-handler)
# Adapted to Teams by : github.com/buckmalibu (https://github.com/buckmalibu/gke-notification-handler-teams)
# =============================================================================
"""
This script processes GKE cluster upgrade-related notifications as part of a
GCP Cloud Function.
"""
# =============================================================================
# Imports
# =============================================================================
import base64
import json
import os
import requests
import sys


def process_event(teams_data, webhook_url):
    byte_length = str(sys.getsizeof(teams_data))
    headers = {
        "Content-Type": "application/json",
        "Content-Length": byte_length,
    }
    response = requests.post(webhook_url, data=json.dumps(teams_data), headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)


def notify_teams(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """

    print(
        """This Function was triggered by messageId {} published at {}
    """.format(
            context.event_id, context.timestamp
        )
    )

    try:
        if "data" in event:
            # Print the event at the beginning for easier debug.
            print("Event was passed into function and will be processed.")
            print(event)
           # Shared Variables
            if not "attributes" in event:
                raise KeyError("no attributes exist")
            cluster = event["attributes"].get("cluster_name")
            cluster_resource = json.loads(event["attributes"]["payload"]).get("resourceType")
            location = event["attributes"].get("cluster_location")
            message = base64.b64decode(event["data"]).decode("utf-8")
            project = event["attributes"].get("project_id")
            webhook_url = os.getenv("TEAMS_WEBHOOK_URL")

            # UpgradeEvent
            if "UpgradeEvent" in event["attributes"]["type_url"]:
                # UpgradeEvent Variables
                current_version = json.loads(event["attributes"]["payload"]).get("currentVersion")
                start_time = json.loads(event["attributes"]["payload"]).get("operationStartTime")
                target_version = json.loads(event["attributes"]["payload"]).get("targetVersion")
                title = f"GKE Cluster Upgrade Notification"
                teams_data = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0076D7",
                    "summary": title,
                    "sections": [{
                        "activityTitle": title,
                        "activitySubtitle": cluster,
                        "activityImage": "https://lh3.googleusercontent.com/Aane0AssTO_QZK7MZ3yV89oPg95K5LgJ7Keang1B9Vi1DEMWG4vTUqBewXM3ibwZdEO0IW1NnumogaGOZVwf=w80-h80",
                        "facts": [{
                            "name": "Project",
                            "value": project
                            },
                            {
                            "name": "Cluster",
                            "value": cluster
                            },
                            {
                            "name": "Location",
                            "value": location
                            },
                            {
                            "name": "Update Type",
                            "value": cluster_resource
                            },
                            {
                            "name": "Current Version",
                            "value": current_version
                            },
                            {
                            "name": "Target Version",
                            "value": target_version
                            },
                            {
                            "name": "Start Time",
                            "value": start_time
                            },
                            {
                            "name": "Details",
                            "value": message
                            }
                            ],
                    }],
                }
                process_event(teams_data, webhook_url)
            # UpgradeAvailableEvent
            elif "UpgradeAvailableEvent" in event["attributes"]["type_url"]:
                if os.getenv("SEND_UPGRADE_AVAILABLE_NOTIFICATIONS") == "enabled":
                    # UpgradeAvailableEvent Variables
                    available_version = json.loads(event["attributes"]["payload"]).get("version")
                    title = f"GKE Cluster Upgrade Available Notification"
                    teams_data = {
                        "@type": "MessageCard",
                        "@context": "http://schema.org/extensions",
                        "themeColor": "0076D7",
                        "summary": title,
                        "sections": [{
                            "activityTitle": title,
                            "activitySubtitle": cluster,
                            "activityImage": "https://lh3.googleusercontent.com/Aane0AssTO_QZK7MZ3yV89oPg95K5LgJ7Keang1B9Vi1DEMWG4vTUqBewXM3ibwZdEO0IW1NnumogaGOZVwf=w80-h80",
                            "facts": [{
                                "name": "Project",
                                "value": project
                                },
                                {
                                "name": "Cluster",
                                "value": cluster
                                },
                                {
                                "name": "Location",
                                "value": location
                                },
                                {
                                "name": "Eligible Resource",
                                "value": cluster_resource
                                },
                                {
                                "name": "Eligible Version",
                                "value": available_version
                                },
                                {
                                "name": "Details",
                                "value": message
                                }
                                ],
                        }],
                    }
                    process_event(teams_data, webhook_url)
                else:
                    pass
            else:
                print(
                    "Event was neither UpgradeEvent or UpgradeAvailableEvent, so it will be skipped."
                )
                exit(0)
        else:
            print("No event was passed into the function. Exiting.")
            exit(0)
    except (KeyError):
        print("Key Not Found!", KeyError)
    except Exception as e:
        print(e)

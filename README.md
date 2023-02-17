# gke-notification-handler-teams

(Forked from echoboomer/gke-notification-handler - for Slack)
A Cloud Function that will parse GKE cluster upgrade notifications (and upgrade available notifications) and send them to Teams.

This is a Python script meant to run in a GCP Cloud Function.

The two files here `main.py` and `requirements.txt` can be compiled into a `zip` file called `main.py.zip` and placed in a GCS bucket for retrieval by the function. Optionally, you can configure a source repo.

## Setup

You'll need a Teams team with an incoming webhook configured for whichever channel you'd like to receive these notifications.

You're free to tweak this as needed to make it work for your use case.

## Environment Variables

- `SEND_UPGRADE_AVAILABLE_NOTIFICATIONS` - if set to `enabled`, notifications will be sent regarding `UpgradeAvailableEvent` types. This can be verbose and annoying, so it is configurable.
- `TEAMS_WEBHOOK_URL` - should contain the webhook for sending to Teams.

## Dependencies and Examples

- You must have a Pub/Sub topic available to handle notifications from a given GKE cluster:

```hcl
resource "google_pubsub_topic" "gke_cluster_upgrade_notifications" {
  name    = "gke-cluster-upgrade-notifications"
  project = "example-1234"

  labels = {
    ...
  }

  message_storage_policy {
    allowed_persistence_regions = [
      "region",
    ]
  }
}
```

Alternatively, you can create this in the UI or via `gcloud`.

- You must also configure your cluster to send notifications to the topic when upgrade events are triggered. This is currently available for configuration via Terraform in the `google-beta` provider:

```hcl
resource "google_container_cluster" "cluster" {
  provider = google-beta

  ...

  notification_config {
    pubsub {
      enabled = true
      topic   = "name-of-pubsub-topic"
    }
  }
}
```

Alternatively, you can enable this on a cluster via `gcloud`. More context available [here](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-upgrade-notifications#enabling_upgrade_notifications).

- Finally, you'll need to deploy the Cloud Function:
  
```hcl
resource "google_cloudfunctions_function" "gke_cluster_upgrade_notifications" {
  name        = "gke-cluster-upgrade-notifications"
  description = "Sends notifications to Teams for GKE cluster upgrade notifications."
  runtime     = "python38"

  available_memory_mb   = 128
  entry_point           = "notify_teams"
  ingress_settings      = "ALLOW_INTERNAL_ONLY"
  source_archive_bucket = "gcs-bucket-name"
  source_archive_object = "main.py.zip"
  timeout               = 30

  environment_variables = {
    TEAMS_WEBHOOK_URL = "foo"
  }

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.gke_cluster_upgrade_notifications.id
    failure_policy {
      retry = true
    }
  }

  labels = {
    ...
  }
}
```

Alternatively, you can create this in the UI or via `gcloud`. You can interpet the important bits from the example above.

**Note:** The Terraform examples are only provided as a starting point.

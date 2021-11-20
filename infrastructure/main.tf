terraform {
  backend "remote" {
    organization = "jcampbell"

    workspaces {
      name = "gull-cannon"
    }
  }
}

provider "google" {
  region = "us-east1"
}

module "project-factory" {
  source  = "terraform-google-modules/project-factory/google"
  version = "~> 10.1"

  name              = "gull-cannon"
  random_project_id = true
  org_id            = "1077903016582"
  billing_account   = "0167E9-D67CAC-E98E9B"

  activate_apis = ["cloudtasks.googleapis.com", "cloudfunctions.googleapis.com"]
  # ,"appengine.googleapis.com", "pubsub.googleapis.com", "logging.googleapis.com",
}

locals {
  root_dir  = abspath("../cloud-function")
  timestamp = formatdate("YYMMDDhhmmss", timestamp())
}

data "archive_file" "source" {
  type        = "zip"
  source_dir  = local.root_dir
  output_path = "/tmp/function-${local.timestamp}.zip"
}

resource "google_storage_bucket" "bucket" {
  name     = "cf.gull-cannon.baserate.org"
  location = "US"
  project  = module.project-factory.project_id
}

resource "google_storage_bucket_object" "archive" {
  name    = "handler.zip"
  bucket  = google_storage_bucket.bucket.name
  source  = data.archive_file.source.output_path
}

resource "google_cloudfunctions_function" "function" {
  project = module.project-factory.project_id

  name        = "gull-cannon"
  description = "gull-cannon logger"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  trigger_http          = true
  entry_point           = "handler"
  environment_variables = {
    CONNECTION_STRING = var.CONNECTION_STRING
  }
}

# IAM entry for all users to invoke the function
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.function.project
  region         = google_cloudfunctions_function.function.region
  cloud_function = google_cloudfunctions_function.function.name

  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}


terraform {
  backend "remote" {
    organization = "jcampbell"

    workspaces {
      name = "gull-cannon"
    }
  }
}

provider "google" {
  alias   = "baserate"
  project = "warm-drive-332522"
  region  = "us-east1"
}

provider "google" {
  project      = module.project-factory.project_id
  region       = "us-east-1"
  access_token = data.google_service_account_access_token.default.access_token
}

data "google_service_account_access_token" "default" {
  provider               = "google.baserate"
  target_service_account = module.project-factory.api_s_account_fmt
  scopes                 = ["userinfo-email", "cloud-platform"]
  lifetime               = "300s"
}

module "project-factory" {
  provider  = google.baserate
  source    = "terraform-google-modules/project-factory/google"
  version   = "~> 10.1"

  name              = "gull-cannon"
  random_project_id = true
  org_id            = "1077903016582"
  billing_account   = "0167E9-D67CAC-E98E9B"

  activate_apis = ["cloudtasks.googleapis.com", "cloudfunctions.googleapis.com"]
  # , "pubsub.googleapis.com", "logging.googleapis.com",
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
  name     = "project-bucket"
  location = "US"
}

resource "google_storage_bucket_object" "archive" {
  name   = "handler.zip"
  bucket = google_storage_bucket.bucket.name
  source = data.archive_file.source.output_path
}

resource "google_cloudfunctions_function" "function" {
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

variable "CONNECTION_STRING" {
  type      = string
  sensitive = true
}

output "trigger_url" {
  value = google_cloudfunctions_function.function.https_trigger_url
}

output "project_name" {
  value = module.project-factory.project_name
}

output "project_id" {
  value = module.project-factory.project_id
}

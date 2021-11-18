terraform {
  backend "remote" {
    organization = "jcampbell"

    workspaces {
      name = "gull-cannon"
    }
  }
}

provider "google" {
  project     = "gullcannon"
  region      = "us-east1"
}

module "project-factory" {
  source  = "terraform-google-modules/project-factory/google"
  version = "~> 10.1"

  name                 = "gull-cannon"
  random_project_id    = true
  usage_bucket_name    = "gull-cannon-usage-report-bucket"
  usage_bucket_prefix  = "gull-cannon/1/integration"
  org_id               = "1077903016582"
  billing_account      = "0167E9-D67CAC-E98E9B"

  activate_apis = ["cloudtasks.googleapis.com", "cloudfunctions.googleapis.com"]
  # , "pubsub.googleapis.com", "logging.googleapis.com",
}
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
  org_id               = "1077903016582"
  billing_account      = "0167E9-D67CAC-E98E9B"

  activate_apis = ["cloudtasks.googleapis.com", "cloudfunctions.googleapis.com"]
  # , "pubsub.googleapis.com", "logging.googleapis.com",
}

variable "GOOGLE_CREDENTIALS" {  # PLACEHOLDER --> this should never be used
  type                 = string
  sensitive            = true
}

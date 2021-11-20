output "trigger_url" {
  value = google_cloudfunctions_function.function.https_trigger_url
}

output "project_name" {
  value = module.project-factory.project_name
}

output "project_id" {
  value = module.project-factory.project_id
}

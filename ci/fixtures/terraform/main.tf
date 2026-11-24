terraform {
  required_version = "= 1.17.1"
}

resource "terraform_data" "documented" {
  input = "runner-terraform"
}

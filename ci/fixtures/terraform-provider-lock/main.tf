terraform {
  required_version = "= 1.17.1"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "= 3.6.3"
    }
  }
}

resource "random_pet" "acceptance" {
  length = 2
}

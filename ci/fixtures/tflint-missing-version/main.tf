terraform {}

resource "terraform_data" "linted" {
  input = "runner-terraform"
}

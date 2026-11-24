resource "aws_s3_bucket" "insecure" {
  bucket = "runner-terraform-trivy-fixture"
}

resource "aws_s3_bucket_public_access_block" "insecure" {
  bucket                  = aws_s3_bucket.insecure.id
  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

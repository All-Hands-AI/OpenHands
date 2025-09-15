#!/bin/bash
# process-template.sh
# Process HTML template with token substitution for release reports

set -e

# Function to display usage
usage() {
    echo "Usage: $0 <template_file> <output_file> <tag> <bucket> <tag_folder> <download_url> <repository> <run_id> [url_length] [expires_at]"
    echo ""
    echo "Arguments:"
    echo "  template_file  - Path to the HTML template file"
    echo "  output_file    - Path where the processed HTML will be written"
    echo "  tag            - Release tag (e.g., 1.0.0)"
    echo "  bucket         - S3 bucket name"
    echo "  tag_folder     - S3 tag folder (e.g., releases/1.0.0)"
    echo "  download_url   - Presigned download URL"
    echo "  repository     - GitHub repository (e.g., owner/repo)"
    echo "  run_id         - GitHub workflow run ID"
    echo "  url_length     - Length of the download URL (optional)"
    echo "  expires_at     - When the URL expires in ISO 8601 format (optional)"
    echo ""
    echo "Example:"
    echo "  $0 .github/templates/release-report.html output.html 1.0.0 my-bucket releases/1.0.0 'https://...' owner/repo 1234567890 1500 '2024-01-15T12:00:00Z'"
    exit 1
}

# Check arguments
if [ $# -lt 8 ]; then
    echo "❌ Error: Not enough arguments provided"
    usage
fi

TEMPLATE_FILE="$1"
OUTPUT_FILE="$2"
TAG="$3"
BUCKET="$4"
TAG_FOLDER="$5"
DOWNLOAD_URL="$6"
REPOSITORY="$7"
RUN_ID="$8"
URL_LENGTH="${9:-unknown}"
EXPIRES_AT="${10:-unknown}"

# Validate template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "🔄 Processing template..."
echo "  Template: $TEMPLATE_FILE"
echo "  Output: $OUTPUT_FILE"
echo "  Tag: $TAG"
echo "  Bucket: $BUCKET"
echo "  Repository: $REPOSITORY"
echo "  Run ID: $RUN_ID"
echo ""

# Process template with sed substitutions
# Note: We use | as delimiter to avoid conflicts with forward slashes in paths
# We need to escape special characters in the values to prevent sed issues
TAG_ESCAPED=$(printf '%s\n' "$TAG" | sed 's/[[\.*^$()+?{|]/\\&/g')
BUCKET_ESCAPED=$(printf '%s\n' "$BUCKET" | sed 's/[[\.*^$()+?{|]/\\&/g')
TAG_FOLDER_ESCAPED=$(printf '%s\n' "$TAG_FOLDER" | sed 's/[[\.*^$()+?{|]/\\&/g')
DOWNLOAD_URL_ESCAPED=$(printf '%s\n' "$DOWNLOAD_URL" | sed 's/[[\.*^$()+?{|]/\\&/g')
REPOSITORY_ESCAPED=$(printf '%s\n' "$REPOSITORY" | sed 's/[[\.*^$()+?{|]/\\&/g')
RUN_ID_ESCAPED=$(printf '%s\n' "$RUN_ID" | sed 's/[[\.*^$()+?{|]/\\&/g')
URL_LENGTH_ESCAPED=$(printf '%s\n' "$URL_LENGTH" | sed 's/[[\.*^$()+?{|]/\\&/g')
EXPIRES_AT_ESCAPED=$(printf '%s\n' "$EXPIRES_AT" | sed 's/[[\.*^$()+?{|]/\\&/g')

# Perform substitutions using | as delimiter to avoid conflicts with forward slashes
sed -e "s|{{TAG}}|$TAG_ESCAPED|g" \
    -e "s|{{BUCKET}}|$BUCKET_ESCAPED|g" \
    -e "s|{{TAG_FOLDER}}|$TAG_FOLDER_ESCAPED|g" \
    -e "s|{{DOWNLOAD_URL}}|$DOWNLOAD_URL_ESCAPED|g" \
    -e "s|{{REPOSITORY}}|$REPOSITORY_ESCAPED|g" \
    -e "s|{{RUN_ID}}|$RUN_ID_ESCAPED|g" \
    -e "s|{{TIMESTAMP}}|$TIMESTAMP|g" \
    -e "s|{{URL_LENGTH}}|$URL_LENGTH_ESCAPED|g" \
    -e "s|{{EXPIRES_AT}}|$EXPIRES_AT_ESCAPED|g" \
    "$TEMPLATE_FILE" > "$OUTPUT_FILE"

# Verify the output file was created and has content
if [ ! -f "$OUTPUT_FILE" ] || [ ! -s "$OUTPUT_FILE" ]; then
    echo "❌ Error: Failed to create output file or file is empty"
    exit 1
fi

# Check that substitutions worked by looking for remaining template tokens
if grep -q "{{" "$OUTPUT_FILE"; then
    echo "⚠️  Warning: Some template tokens were not replaced:"
    grep -o "{{[^}]*}}" "$OUTPUT_FILE" | sort -u
fi

echo "✅ Template processed successfully: $OUTPUT_FILE"
echo "  Output size: $(wc -c < "$OUTPUT_FILE") bytes"
echo "  Output lines: $(wc -l < "$OUTPUT_FILE") lines"

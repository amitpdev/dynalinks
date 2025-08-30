# Justfile for the DynaLinks project

# Default command to run when no command is specified
default: list

list:
    just --list

# Create a virtual environment using uv
# uv will use the Python version currently active (e.g., from pyenv)
venv:
    uv venv

activate:
    source .venv/bin/activate.fish

# Install Python dependencies from requirements.txt using uv
# Make sure to activate the virtual environment first: `source .venv/bin/activate`
install:
    uv pip install -r requirements.txt

# A convenience command to create the venv and install dependencies, and print next steps
setup: venv activate install

# Sync the virtual environment with requirements.txt (removes unused packages)
sync:
    uv pip sync requirements.txt

# Remove the virtual environment to delete all dependencies
clean:
    rm -rf .venv

# Reinstall all dependencies from scratch
reinstall: clean setup

# Run the FastAPI application with auto-reloading
run:
    uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

# Run the test suite using pytest
test:
    pytest

# Start the Docker Compose services in detached mode
docker-up:
    docker-compose up -d

# Stop and remove the Docker Compose services
docker-down:
    docker-compose down

# Follow the logs of the Docker Compose services
docker-logs:
    docker-compose logs -f

# Load the database schema from schema.sql into the Dockerized database
# Note: This requires the Docker services to be running (use `just docker-up`)
db-schema-load:
    cat schema.sql | docker-compose exec -T db psql -U dynalinks_user -d dynalinks_db

# Initialize the database by starting Docker and loading the schema
db-init: docker-up db-schema-load

# ------------------------------------------------------------------------------
# API INTERACTION
# ------------------------------------------------------------------------------
# Note: Ensure the API is running with `just run` before using these commands.
# For pretty-printed JSON output, make sure you have `jq` installed.

# Create a new dynamic link.
# Usage: just api-create-link "https://example.com/my-fallback-url"
api-create-link fallback_url:
    @echo "Creating a new dynamic link..."
    @curl -s -X POST "http://localhost:8000/api/v1/links/" \
        -H "Content-Type: application/json" \
        -d '{"fallback_url": "{{fallback_url}}"}'

# Create a new dynamic link with a custom short code.
# Usage: just api-create-link-custom "https://example.com/fallback" "mycode"
api-create-link-custom fallback_url code:
    @echo "Creating a new dynamic link with custom code '{{code}}'..."
    @curl -s -X POST "http://localhost:8000/api/v1/links/?custom_code={{code}}" \
        -H "Content-Type: application/json" \
        -d '{"fallback_url": "{{fallback_url}}"}'

# List all dynamic links.
api-list-links:
    @echo "Listing all dynamic links..."
    @curl -s "http://localhost:8000/api/v1/links/"

# Get a specific dynamic link by its short code.
# Usage: just api-get-link "shortcode"
api-get-link short_code:
    @echo "Getting dynamic link with short code '{{short_code}}'..."
    @curl -s "http://localhost:8000/api/v1/links/{{short_code}}"

# Update a dynamic link. The second argument is a JSON string.
# Usage: just api-update-link "shortcode" '{"title": "New Cool Title"}'
api-update-link short_code data:
    @echo "Updating dynamic link '{{short_code}}'..."
    @curl -s -X PUT "http://localhost:8000/api/v1/links/{{short_code}}" \
        -H "Content-Type: application/json" \
        -d '{{data}}'

# Deactivate (soft delete) a dynamic link.
# Usage: just api-delete-link "shortcode"
api-delete-link short_code:
    @echo "Deactivating dynamic link '{{short_code}}'..."
    @curl -s -X DELETE "http://localhost:8000/api/v1/links/{{short_code}}"

# Generate a QR code for a dynamic link and save it to a file.
# Usage: just api-qr-code "shortcode"
api-qr-code short_code:
    @echo "Generating QR code for '{{short_code}}'..."
    @curl -s -o "qr_{{short_code}}.png" "http://localhost:8000/api/v1/links/{{short_code}}/qr"
    @echo "QR code saved to qr_{{short_code}}.png"

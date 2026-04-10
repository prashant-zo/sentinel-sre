# Sentinel DevOps

[![CI](https://github.com/prashant-zo/sentinel-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/prashant-zo/sentinel-devops/actions/workflows/ci.yml)
[![Deploy](https://github.com/prashant-zo/sentinel-devops/actions/workflows/deploy.yml/badge.svg)](https://github.com/prashant-zo/sentinel-devops/actions/workflows/deploy.yml)

A practical reference project for self-healing container workloads:

- A small `Flask` app serves traffic and exposes a health endpoint.
- A monitor service checks health and restarts the app container on failure.
- `Terraform` provisions AWS infrastructure.
- `Ansible` configures the server and runs the Compose stack.
- `GitHub Actions` handles CI and deployment automation.

## Table of contents

- [What this project demonstrates](#what-this-project-demonstrates)
- [Architecture at a glance](#architecture-at-a-glance)
- [Quick start (local)](#quick-start-local)
- [Endpoints](#endpoints)
- [Project structure](#project-structure)
- [Self-heal flow](#self-heal-flow)
- [CI/CD workflow](#cicd-workflow)
- [AWS and Terraform notes](#aws-and-terraform-notes)
- [Create Terraform backend resources](#create-terraform-backend-resources)
- [Challenges overcome](#challenges-overcome)
- [Required GitHub secrets](#required-github-secrets)

## What this project demonstrates

This repository shows how to run a small service with automated recovery and deployment:

1. Run the app locally with Docker Compose.
2. Simulate failure (`/crash`) and verify monitor-driven restart.
3. Provision AWS infra with Terraform.
4. Deploy app + monitor with Ansible from CI.

## Architecture at a glance

```text
Client -> Flask app (:5000)
           |
           v
        /health
           ^
           |
Monitor container (polls health)
   -> Docker socket
   -> restart app container on unhealthy state
```

## Quick start (local)

### Prerequisites

- Docker + Docker Compose plugin installed
- Ability to run `docker compose` locally

### Run

```bash
git clone https://github.com/prashant-zo/sentinel-devops.git
cd sentinel-devops
docker compose up -d --build
```

Open `http://localhost:5000` in your browser.

### Verify self-healing

```bash
docker logs -f sentinel-monitor
curl http://localhost:5000/crash
```

After `/crash`, monitor logs should show detection and container restart.

## Endpoints

| Route | Purpose |
| --- | --- |
| `/` | Home page / service response |
| `/health` | Health JSON used by monitor |
| `/crash` | Simulates process failure for testing restart |

## Project structure

```text
app/                      Flask app (port 5000)
monitor/                  Health checker + Docker restart logic
docker-compose.yml        Local orchestration for app + monitor
infra/                    Terraform for AWS (EC2, SG, key pair, backend)
ansible/setup.yml         Server bootstrap + Compose deployment
.github/workflows/ci.yml      Lint + image build
.github/workflows/deploy.yml  Terraform apply + Ansible deploy
```

## Self-heal flow

`sentinel-monitor` is configured with:

- `APP_URL`: target health endpoint URL
- `CONTAINER_NAME`: app container to restart
- `CHECK_INTERVAL`: polling interval (5s in Compose setup)

Monitor behavior:

1. Poll `APP_URL` regularly.
2. Treat failed requests or non-success health as unhealthy.
3. Restart `CONTAINER_NAME` through Docker API (`/var/run/docker.sock`).

## CI/CD workflow

### CI (`.github/workflows/ci.yml`)

Triggered on `push` and `pull_request` to `main`:

- Python `3.9`
- `flake8` on `app/` and `monitor/` (`--select=E9,F63,F7,F82`)
- `docker compose build`

### Deploy (`.github/workflows/deploy.yml`)

Triggered on push to `main`:

1. Set up SSH key from secret.
2. Run Terraform to provision/update infrastructure.
3. Read EC2 public IP via `terraform output -raw server_public_ip`.
4. Generate Ansible inventory.
5. Run `ansible-playbook` to deploy containers.

## AWS and Terraform notes

- Region default: `ap-south-1`
- EC2 defaults: Ubuntu 22.04, `t2.micro`
- Security group allows SSH (`22`) and app access (`5000`)
- Key pair uses `~/.ssh/sentinel_key.pub`
- Terraform state is remote in S3 with encryption and lockfile usage

Important: the S3 backend bucket must already exist and IAM permissions must allow backend operations before `terraform init` can succeed.

## Create Terraform backend resources

Use these commands to create:

- An S3 bucket for the `terraform.tfstate` state file.
- A DynamoDB table for state locking (prevents simultaneous state updates from GitHub Actions and your local machine).

```bash
aws s3api create-bucket \
    --bucket sentinel-tf-state-prashant-12345 \
    --region ap-south-1

aws s3api put-bucket-versioning \
    --bucket sentinel-tf-state-prashant-12345 \
    --versioning-configuration Status=Enabled

aws dynamodb create-table \
    --table-name sentinel-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-south-1
```

## Challenges overcome

- **Terraform Output Masking in CI/CD:** When passing the dynamically generated AWS EC2 IP address from Terraform to Ansible in GitHub Actions, the default `hashicorp/setup-terraform` wrapper masked the raw output. I debugged this and resolved it by disabling the wrapper (`terraform_wrapper: false`) to pass a clean IP to the dynamic Ansible inventory.
- **State File Conflicts:** I realized local Terraform state would cause duplicate servers to be created by GitHub Actions. I successfully migrated the local state to an **AWS S3 Backend** with DynamoDB locking to ensure the pipeline is idempotent and production-ready.

## Required GitHub secrets

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SSH_PRIVATE_KEY`

Deploy workflow writes the private key to `~/.ssh/sentinel_key`, then derives the public key via:

```bash
ssh-keygen -y -f ~/.ssh/sentinel_key > ~/.ssh/sentinel_key.pub
```

## Author

Prashant

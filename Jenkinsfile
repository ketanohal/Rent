pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ketanohal/nivassetudcimage"
        DOCKER_TAG = "latest"
        DOCKER_REGISTRY = "docker.io"  // The Docker Hub registry
        DOCKER_CREDS = 'docker-hub-credentials'  // Jenkins credentials ID for Docker Hub
    }

    stages {
        stage('Checkout') {
            steps {
                // Clone the repository
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                // Build the Docker image
                sh 'docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} .'
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    // Log in to DockerHub and push the image
                    docker.withRegistry('https://docker.io', DOCKER_CREDS) {
                        sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}'
                    }
                }
            }
        }

        stage('Clean Docker') {
            steps {
                // Clean up Docker images and containers to save space
                sh 'docker system prune -f --volumes'
            }
        }
    }

    post {
        always {
            // Clean up Docker after the build process
            sh 'docker system prune -f'
        }
    }
}

pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ketanohal/nivassetudcimage"
        DOCKER_TAG = "latest"
        DOCKER_REGISTRY = "docker.io"  // The Docker Hub registry
    }

    stages {
        stage('Checkout') {
            steps {
                // Clone the repository
                checkout scm
            }
        }

        stage('Clean Docker') {
            steps {
                script {
                    // Clean up Docker images and containers
                    sh 'docker system prune -f --volumes'
                }
            }
        }

        stage('Clean Workspace') {
            steps {
                script {
                    // Clean Jenkins workspace to clear old files/logs
                    cleanWs()
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    // Build the Docker image in the root directory where the Dockerfile is present
                    sh 'docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} .'
                }
            }
        }

        stage('Test') {
            steps {
                // Example: Run tests (adjust this according to your needs)
                script {
                    echo 'Running Tests...'
                    // Add your test commands here (e.g., `sh 'pytest'` for Python tests)
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    // Use Docker Hub credentials to log in and push the image
                    docker.withRegistry('https://docker.io', 'docker-hub-credentials') {
                        // Push the Docker image to Docker Hub
                        sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}'
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    // Example: Deploy to the server or any platform (adjust this)
                    echo 'Deploying Application...'
                    // You can use ssh commands or any other deployment method here
                    // For example, using docker-compose or kubectl for deployment
                }
            }
        }
    }

    post {
        always {
            // Clean up Docker images after the build
            sh 'docker system prune -f'
        }
    }
}

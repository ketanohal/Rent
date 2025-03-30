pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ketanohal/nivassetudcimage"
        DOCKER_TAG = "latest"
        DOCKER_REGISTRY = "ketanohal"  // Your Docker Hub username
    }

    stages {
        stage('Checkout') {
            steps {
                // Clone the repository
                checkout scm
            }
        }

        stage('Build') {
            steps {
                script {
                    // Build the Docker image
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
                    // Push the Docker image to DockerHub
                    sh 'docker login -u $DOCKER_REGISTRY -p $DOCKER_PASSWORD'
                    sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}'
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

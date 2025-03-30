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
                    // Clean up Docker images and containers with sudo
                    sh 'sudo docker system prune -f --volumes'
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

        stage('Docker Test') {
            steps {
                script {
                    // Check Docker version and the PATH for debugging
                    echo 'Checking Docker version...'
                    sh 'sudo docker --version'
                    echo 'Checking PATH...'
                    sh 'echo $PATH'
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    // Build the Docker image using sudo
                    sh 'sudo docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} .'
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo 'Running Tests...'
                    // Example: Run tests (adjust this according to your needs)
                    // Add your test commands here (e.g., `sh 'sudo docker ps'` for testing Docker status)
                    sh 'sudo docker ps'
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    // Use Docker Hub credentials to log in and push the image
                    docker.withRegistry('https://docker.io', 'docker-hub-credentials') {
                        // Push the Docker image to Docker Hub with sudo
                        sh 'sudo docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}'
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
            // Clean up Docker images after the build with sudo
            sh 'sudo docker system prune -f'
        }
    }
}

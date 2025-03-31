pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ketanohal/nivassetudcimage"
        DOCKER_TAG = "latest"
        DOCKER_REGISTRY = "docker.io"
        DOCKER_CREDS = 'docker-hub-credentials-id'  // Jenkins credentials ID for Docker Hub
        CONTAINER_NAME = "nivassetudccontainer"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} .'
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDS) {
                        sh 'docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}'
                    }
                }
            }
        }

        stage('Deploy Latest Image') {
            steps {
                script {
                    // Stop and remove the old container if running
                    sh """
                        docker stop ${CONTAINER_NAME} || true
                        docker rm ${CONTAINER_NAME} || true
                    """

                    // Pull the latest image
                    sh "docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}"

                    // Run the latest image
                    sh """
                        docker run -d -p 5000:5000 --name ${CONTAINER_NAME} ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }

        stage('Clean Docker') {
            steps {
                sh 'docker system prune -f --volumes'
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f'
        }
    }
}

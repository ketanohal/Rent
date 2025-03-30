pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ketanohal/nivassetudcimage"
        DOCKER_TAG = "latest"
        DOCKER_REGISTRY = "docker.io"
        DOCKER_CREDS = 'docker-hub-credentials-id'  // Jenkins credentials ID for Docker Hub
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

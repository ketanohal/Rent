pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'your-dockerhub-username'
        DOCKERHUB_PASS = 'your-dockerhub-password'
        IMAGE_NAME = 'your-dockerhub-username/webapp'
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', credentialsId: 'github-credentials', url: 'https://github.com/ketanohal/your-repo.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh 'docker build -t $IMAGE_NAME:latest .'
                }
            }
        }

        stage('Push Image to DockerHub') {
            steps {
                script {
                    sh 'echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin'
                    sh 'docker push $IMAGE_NAME:latest'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f k8s-deployment.yaml'
            }
        }
    }
}

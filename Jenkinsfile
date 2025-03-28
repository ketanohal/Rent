pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'ketanohal'
        DOCKERHUB_PASS = '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'
        IMAGE_NAME = 'ketanohal/Rent'
    }

        stages {
        stage('Clone Repository') {
            steps {
                git branch: 'master', url: 'https://github.com/ketanohal/Rent.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $ketanohal/rent:first'
            }
        }

        stage('Login to DockerHub') {
            steps {
                sh 'echo $DOCKERHUB_PASS | docker login -u $DOCKERHUB_USER --password-stdin'
            }
        }

        stage('Push to DockerHub') {
            steps {
                sh 'docker push $ketanohal/rent:first'
            }
        }
    }
}

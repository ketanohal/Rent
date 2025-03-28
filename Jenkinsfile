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
    }
}

pipeline { 
    agent any
    stages {
        stage ('Checkout') {
            steps {
                checkout SCM
            }
        }
        stage ('Build') {
            
            steps {
                sh 'npm install'
            }
        }
        stage ('build') {
            steps {
                sh 'ng build'
            }
        }
    }
}

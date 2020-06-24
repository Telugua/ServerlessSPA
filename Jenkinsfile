pipeline { 
    agent any
    stages {
        stage ('Checkout') {
            steps {
                sh 'git checkout master'
            }
        }

         stage ('Build'){
       parallel {
             stage("Angular Build") {
                  agent {
                      docker { image 'node:10' }
                  } 
                  steps {
                         sh 'echo installing packages'
                         sh 'npm install'
                         sh 'npm install -g @angular/cli@8'
                         sh 'echo Building Angular Project'
                         sh 'ng build'
                  }
             }   
            
        }
        
         }
    }
}


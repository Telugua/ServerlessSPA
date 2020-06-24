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
                      container { 'node:latest' }
                  }
                  steps {
                         echo "Installing packages"
                      
                         sh '''
                                npm install
                                npm install -g @angular/cli@8
                         
                                echo "Building Angular Project"
                                ng build
                         '''
                  }
             }   
            
        }
        
         }
    }
}


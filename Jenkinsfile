pipeline { 
    agent any
    stages {
        stage ('Checkout') {
            steps {
                checkout scm
            }
        

         stage ('Build'){
       parallel {
             stage("Angular Build") {
                  agent {
                      docker { image 'node:10' }
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
}

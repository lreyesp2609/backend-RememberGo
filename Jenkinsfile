pipeline {
    agent any

    stages {
        stage('Deploy') {
            steps {
                withCredentials([file(credentialsId: 'remembergo-env', variable: 'ENV_FILE')]) {
                    sh '''
                        # Copiar las credenciales seguras al archivo .env
                        cp "$ENV_FILE" .env
                        
                        # Apagar contenedores anteriores limpiando huérfanos
                        docker compose down --remove-orphans || true
                        
                        # Recompilar y levantar los servicios
                        docker compose up -d --build
                    '''
                }
            }
        }
    }
}

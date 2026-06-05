pipeline {
    agent any

    stages {
        stage('Deploy') {
            steps {
                withCredentials([file(credentialsId: 'remembergo-env', variable: 'REMEMBERGO_ENV_FILE')]) {
                    sh '''
                        # Copiar las credenciales seguras al archivo .env
                        cp "$REMEMBERGO_ENV_FILE" .env
                        
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

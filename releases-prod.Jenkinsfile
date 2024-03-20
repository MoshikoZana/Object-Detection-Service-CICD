pipeline {
    agent any

    parameters {
        string(name: 'POLYBOT_PROD_IMAGE_URL', defaultValue: '', description: '')
    }

    stages {
        stage('Update YAML') {
            steps {
                sh """
                withCredentials([usernamePassword(credentialsId: 'github', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                git checkout releases
                git merge main

                sed -i "s|image: .*|image: $POLYBOT_PROD_IMAGE_URL|g" k8s/prod/polybot.yaml

                git add k8s/prod/polybot.yaml
                git commit -m "$POLYBOT_PROD_IMAGE_URL"
                git push https://moshikozana:$PASSWORD@github.com/MoshikoZana/Object-Detection-Service-CICD.git releases
                """
            }
        }
    }
}
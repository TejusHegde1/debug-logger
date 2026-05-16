pipeline {
    agent any

    environment {
        REGISTRY    = 'local-demo'   // Using a local tag for the Mac demo
        FRONTEND    = "${REGISTRY}/debug-frontend"
        BACKEND     = "${REGISTRY}/debug-backend"
        IMAGE_TAG   = "${BUILD_ID}"
    }

    stages {

        stage('Checkout') {
            steps {
                // Pull latest code (triggered by GitHub Webhook)
                checkout scm
            }
        }

        stage('Build') {
            steps {
                // Build Backend image locally (no push required for local K8s demo)
                dir('backend') {
                    sh "docker build -t ${BACKEND}:${IMAGE_TAG} ."
                    sh "docker tag ${BACKEND}:${IMAGE_TAG} ${BACKEND}:latest"
                }
                // Build Frontend image locally
                dir('frontend') {
                    sh "docker build -t ${FRONTEND}:${IMAGE_TAG} ."
                    sh "docker tag ${FRONTEND}:${IMAGE_TAG} ${FRONTEND}:latest"
                }
            }
        }

        stage('Test') {
            steps {
                // Run pytest directly inside the freshly built Docker container!
                sh "docker run --rm ${BACKEND}:${IMAGE_TAG} pytest test_main.py -v"
            }
        }

        // ── Optional: Automated UI Testing with Selenium ──
        // Uncomment this stage if you want headless browser testing
        /*
        stage('UI Test') {
            steps {
                sh 'kubectl create namespace test-${BUILD_ID} --dry-run=client -o yaml | kubectl apply -f -'
                sh 'kubectl -n test-${BUILD_ID} apply -f k8s/'
                sh 'sleep 30'  // Wait for pods to be ready
                dir('tests') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install selenium
                        python3 selenium_test.py
                    '''
                }
                sh 'kubectl delete namespace test-${BUILD_ID}'
            }
        }
        */

        stage('Deploy') {
            steps {
                // Update the Kubernetes deployments with new images
                sh "kubectl set image deployment/backend backend=${BACKEND}:${IMAGE_TAG}"
                sh "kubectl set image deployment/frontend frontend=${FRONTEND}:${IMAGE_TAG}"
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline succeeded! Build #${BUILD_ID} deployed."
        }
        failure {
            echo "❌ Pipeline failed at build #${BUILD_ID}."
        }
        always {
            cleanWs()
        }
    }
}

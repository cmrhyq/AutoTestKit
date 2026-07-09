pipeline {
    agent {
        kubernetes {
            yaml '''
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: python
                image: python:3.12
                command: [sleep, infinity]
              - name: allure
                image: frankescobar/allure-docker-service
                command: [sleep, infinity]
            '''
        }
    }

    options {
        // 构建超时设置（2小时）
        timeout(time: 2, unit: 'HOURS')
        // 保留最近10次构建
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // 禁用并发构建
        disableConcurrentBuilds()
        // 添加时间戳
        timestamps()
    }

    environment {
        // Python 虚拟环境路径
        PYTHON_ENV = "${WORKSPACE}/venv"
        // 测试环境变量（可通过 Jenkins 参数覆盖）
        TEST_ENV = "${params.TEST_ENV ?: 'test'}"
        // 测试标记（可通过 Jenkins 参数覆盖）
        TEST_MARKERS = "${params.TEST_MARKERS ?: ''}"
        // 并行 worker 数量
        PARALLEL_WORKERS = "${params.PARALLEL_WORKERS ?: 'auto'}"
        // Allure 结果目录
        ALLURE_RESULTS_DIR = "report/allure-results"
        // 报告目录
        REPORT_DIR = "report"
        // Playwright 安装地址
        PLAYWRIGHT_DOWNLOAD_HOST = 'https://npmmirror.com/mirrors/playwright/'
    }

    parameters {
        choice(
            name: 'TEST_ENV',
            choices: ['test', 'dev', 'staging', 'prod'],
            description: '选择测试环境'
        )
        choice(
            name: 'TEST_TYPE',
            choices: ['api', 'ui', 'all', 'smoke', 'regression'],
            description: '选择测试类型'
        )
        string(
            name: 'TEST_MARKERS',
            defaultValue: '',
            description: '自定义测试标记（如：ui and smoke）'
        )
        choice(
            name: 'PARALLEL_WORKERS',
            choices: ['auto', '1', '2', '4', '8'],
            description: '并行执行 worker 数量'
        )
        booleanParam(
            name: 'INSTALL_BROWSERS',
            defaultValue: true,
            description: '是否安装 Playwright 浏览器'
        )
        booleanParam(
            name: 'CLEAN_WORKSPACE',
            defaultValue: true,
            description: '构建后是否清理工作空间'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                container('python') {
                    script {
                        echo "开始拉取代码..."
                        echo "分支: ${env.BRANCH_NAME ?: 'main'}"
                    }
                    checkout scm
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                container('python') {
                    script {
                        echo "设置 Python 环境..."
                        echo "Python 版本: ${sh(script: 'python --version', returnStdout: true).trim()}"
                    }
                    sh '''
                        # 创建虚拟环境（如果不存在）
                        if [ ! -d "${PYTHON_ENV}" ]; then
                            python -m venv ${PYTHON_ENV}
                        fi

                        # 激活虚拟环境并升级 pip
                        . ${PYTHON_ENV}/bin/activate
                        pip install --upgrade pip setuptools wheel

                        # 安装项目依赖
                        pip install -r requirements.txt

                        # 显示已安装的包
                        pip list
                    '''
                }
            }
        }

        stage('Install Playwright Browsers') {
            when {
                anyOf {
                    expression { params.INSTALL_BROWSERS == true }
                    expression { params.TEST_TYPE == 'all' || params.TEST_TYPE == 'ui' }
                }
            }
            steps {
                container('python') {
                    script {
                        echo "安装 Playwright 浏览器驱动..."
                    }
                    sh '''
                        . ${PYTHON_ENV}/bin/activate
                        # 安装 Playwright 浏览器（仅安装 chromium 以节省时间）
                        playwright install chromium
                        # 安装 Playwright 系统依赖
                        playwright install-deps chromium
                        # 如果需要安装所有浏览器，取消下面的注释
                        # playwright install --with-deps
                    '''
                }
            }
        }

        stage('Create Directories') {
            steps {
                container('python') {
                    sh '''
                        # 创建必要的目录并设置权限（解决多容器权限问题）
                        mkdir -p ${REPORT_DIR}/allure-results
                        mkdir -p ${REPORT_DIR}/allure-report
                        mkdir -p logs
                        mkdir -p screenshots
                        # 设置目录权限，确保所有用户可读写
                        chmod -R 777 ${REPORT_DIR}
                        chmod -R 777 logs
                        chmod -R 777 screenshots
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                container('python') {
                    script {
                        def testCommand = buildTestCommand()
                        echo "执行测试命令: ${testCommand}"
                        
                        // 使用 catchError 允许测试失败后继续生成报告
                        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                            sh """
                                . ${PYTHON_ENV}/bin/activate
                                export TEST_ENV=${TEST_ENV}
                                ${testCommand}
                            """
                        }
                        
                        // 测试完成后修复权限，确保 Jenkins agent 可以访问
                        sh '''
                            chmod -R 777 ${REPORT_DIR} || true
                        '''
                    }
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                container('allure') {
                    script {
                        echo "使用 Allure 容器生成报告..."
                    }
                    sh '''
                        # 使用 allure 容器生成 HTML 报告
                        allure generate ${ALLURE_RESULTS_DIR} -o ${REPORT_DIR}/allure-report --clean
                        
                        # 安装 allure-combine 并添加到 PATH
                        pip install allure-combine
                        export PATH="$HOME/.local/bin:$PATH"
                        
                        # 生成单文件 HTML 报告到 report 目录
                        allure-combine ${REPORT_DIR}/allure-report --dest ${REPORT_DIR}
                        
                        # 显示生成的文件
                        ls -la ${REPORT_DIR}/
                    '''
                }
            }
        }

        stage('Archive Test Results') {
            steps {
                script {
                    echo "归档测试结果..."
                }
                // 归档测试结果和报告
                archiveArtifacts artifacts: 'logs/**/*', allowEmptyArchive: true
                archiveArtifacts artifacts: 'screenshots/**/*', allowEmptyArchive: true
                archiveArtifacts artifacts: "${ALLURE_RESULTS_DIR}/**/*", allowEmptyArchive: true
                archiveArtifacts artifacts: "${REPORT_DIR}/allure-report/**/*", allowEmptyArchive: true
                archiveArtifacts artifacts: "${REPORT_DIR}/complete.html", allowEmptyArchive: true
                
                // 发布 HTML 报告（使用 HTML Publisher 插件）
                publishHTML(target: [
                    allowMissing: true,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: "${REPORT_DIR}/allure-report",
                    reportFiles: 'index.html',
                    reportName: 'Allure Report'
                ])
            }
        }
    }

    post {
        always {
            container('python') {
                script {
                    echo "构建完成，清理环境..."
                    
                    // 如果启用清理，则清理工作空间
                    if (params.CLEAN_WORKSPACE) {
                        echo "清理工作空间..."
                        // 只清理临时文件，保留报告和日志
                        sh '''
                            rm -rf ${PYTHON_ENV}
                            rm -rf __pycache__
                            find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
                            find . -type f -name "*.pyc" -delete 2>/dev/null || true
                        '''
                    }
                }
            }
        }

        success {
            script {
                echo "✅ 所有测试通过！"
                // 可以添加成功通知，如邮件、Slack 等
                // emailext(
                //     subject: "✅ 测试通过: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                //     body: "构建成功！\n\n查看详情: ${env.BUILD_URL}",
                //     to: "team@example.com"
                // )
            }
        }

        failure {
            script {
                echo "❌ 测试失败！"
                // 可以添加失败通知
                emailext(
                    subject: "❌ 测试失败: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                    body: "构建失败！\n\n查看详情: ${env.BUILD_URL}\n\n查看日志: ${env.BUILD_URL}console",
                    to: "cmrhyq@163.com"
                )
            }
        }

        unstable {
            script {
                echo "⚠️ 部分测试失败或不稳定！"
            }
        }

        cleanup {
            script {
                echo "清理阶段完成"
            }
        }
    }
}

// 构建测试命令的函数
def buildTestCommand() {
    def baseCommand = "pytest"
    def options = []
    
    // 添加详细输出
    options.add("-v")
    
    // 添加 Allure 结果目录
    options.add("--alluredir=${ALLURE_RESULTS_DIR}")
    options.add("--clean-alluredir")
    
    // 并行执行
    if (PARALLEL_WORKERS != '1') {
        options.add("-n ${PARALLEL_WORKERS}")
    }
    
    // 根据测试类型选择测试路径和标记
    switch(params.TEST_TYPE) {
        case 'ui':
            options.add("tests/ui")
            options.add("-m ui")
            break
        case 'api':
            options.add("tests/api")
            options.add("-m api")
            break
        case 'smoke':
            options.add("tests/")
            options.add("-m smoke")
            break
        case 'regression':
            options.add("tests/")
            options.add("-m regression")
            break
        default:
            options.add("tests/")
            break
    }
    
    // 添加自定义标记
    if (params.TEST_MARKERS?.trim()) {
        options.add("-m \"${params.TEST_MARKERS}\"")
    }
    
    // 添加超时设置（每个测试最多30分钟）
    options.add("--timeout=1800")
    
    // 添加失败重试（最多重试2次）
    options.add("--reruns=2")
    options.add("--reruns-delay=2")
    
    // 组合命令
    return "${baseCommand} ${options.join(' ')}"
}

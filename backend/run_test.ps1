# API测试运行脚本
Write-Host "🚀 启动API测试..." -ForegroundColor Green

# 等待服务器就绪
Write-Host "⏳ 等待服务器启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 检查服务器
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 服务器正在运行" -ForegroundColor Green
    } else {
        Write-Host "⚠️  服务器未响应，请手动启动: python run_dev.py" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "⚠️  无法连接到服务器，请手动启动: python run_dev.py" -ForegroundColor Yellow
    exit 1
}

# 运行测试
Write-Host "`n🧪 开始API测试..." -ForegroundColor Green
python test_api.py

Write-Host "`n✅ 测试完成！" -ForegroundColor Green

